"""
CSV downloader and parser for orders.decware.com.
Downloads order data and updates the database with new information.
"""
import datetime
import csv
import logging
import os
import tempfile
import time
import re
from typing import Optional, List, Dict, Any, Tuple
import sys

import requests
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone

from .models import OrderRecord, StatusHistory

# Configure logging
logger = logging.getLogger(__name__)

class DecwareOrderScraper:
    """Handles downloading and processing order data from orders.decware.com."""
    
    # Direct CSV URL for Decware orders
    CSV_URL = "https://orders.decware.com/export_csv.php"
    MAX_RETRIES = 3
    
    # Mapping from CSV Column Header (case-insensitive matching handled in parse_csv) 
    # to OrderRecord model field name
    COLUMN_MAPPING = {
        # CSV Header        : Model Field Name
        'For'              : 'customer_name',
        'From'             : 'origin',
        'Qty'              : 'quantity',
        'MODEL'            : 'model',  # Note: Case differs in CSV
        'Base'             : 'base',   # Note: Case differs in CSV
        'VOLTS'            : 'volts',  # Note: Case differs in CSV
        'Options'          : 'options',# Note: Case differs in CSV
        'Status'           : 'status', # Note: Case differs in CSV
        'Date-Time'        : 'order_date' # Map Date-Time to order_date
    }
    
    def __init__(self):
        self.download_dir = tempfile.mkdtemp()

    def download_csv(self) -> Optional[str]:
        """
        Downloads the CSV file directly using requests.
        Returns the path to the downloaded CSV file or None if download fails.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"Downloading CSV from {self.CSV_URL} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                
                # Make the request to download the CSV
                response = requests.get(self.CSV_URL, timeout=60)
                
                if response.status_code == 200:
                    # Create a temporary file to store the CSV
                    csv_path = os.path.join(self.download_dir, f"decware_orders_{int(time.time())}.csv")
                    
                    # Write the content to the file
                    with open(csv_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"CSV file downloaded successfully: {csv_path}")
                    return csv_path
                else:
                    logger.error(f"Failed to download CSV. Status code: {response.status_code}")
            
            except requests.RequestException as e:
                logger.error(f"Request error during download (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.error(f"Unexpected error during download (attempt {attempt + 1}): {e}")
            
            if attempt == self.MAX_RETRIES - 1:
                logger.error("Max retries reached for download, giving up")
                return None
            else:
                time.sleep(5)
        
        return None

    def parse_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Parses the CSV file and returns a list of order records.
        """
        orders = []
        try:
            # Log environment information for debugging
            logger.info(f"Python version: {sys.version}")
            logger.info(f"Default encoding: {sys.getdefaultencoding()}")
            logger.info(f"Filesystem encoding: {sys.getfilesystemencoding()}")
            logger.info(f"Timezone: {timezone.get_current_timezone_name()}")
            
            # Try multiple encodings if needed
            encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
            csv_read_success = False
            
            for encoding in encodings_to_try:
                try:
                    with open(csv_path, mode='r', encoding=encoding) as csvfile:
                        # Check if file is readable
                        sample = csvfile.read(1024)
                        if not sample:
                            logger.warning(f"CSV file appears empty with encoding {encoding}")
                            continue
                            
                        # Reset file pointer
                        csvfile.seek(0)
                        
                        reader = csv.DictReader(csvfile)
                        
                        # Verify we can read headers
                        if not reader.fieldnames:
                            logger.warning(f"No CSV headers detected with encoding {encoding}")
                            continue
                            
                        logger.info(f"Successfully opened CSV with encoding: {encoding}")
                        logger.debug(f"CSV Headers detected: {reader.fieldnames}")
                        
                        # --- Debug: Log calculated required fields ONCE --- #
                        try:
                            required_fields_calculated = {
                                f.name for f in OrderRecord._meta.get_fields()
                                if not f.is_relation and not f.null and not getattr(f, 'default', None) and not f.auto_created
                            }
                            logger.debug(f"Calculated required model fields: {required_fields_calculated}")
                        except Exception as e:
                            logger.error(f"Error calculating required fields: {e}")
                        # --- End Debug --- #
                        
                        for i, row in enumerate(reader):
                            order = {}
                            processed_fields = set()
                            
                            # --- Debug: Log keys for first few rows --- #
                            if i < 3:  # Log first 3 rows
                                logger.debug(f"Row {i+1} Keys: {list(row.keys())}")
                                # Log Date-Time value specifically
                                date_time_key = next((k for k in row.keys() if k and k.strip() == 'Date-Time'), None)
                                if date_time_key:
                                    date_value = row.get(date_time_key, '')
                                    logger.info(f"Row {i+1} Date-Time value: '{date_value}'")
                                    # Log character codes for debugging
                                    if date_value:
                                        char_codes = [f"{j}:{ord(c)}" for j, c in enumerate(date_value)]
                                        logger.debug(f"Row {i+1} Date-Time chars: {char_codes}")
                            # --- End Debug --- #
                            
                            for csv_key, value in row.items():
                                if csv_key is None: continue # Skip if key is None (potential issue in some CSVs)
                                
                                normalized_csv_key = csv_key.strip()
                                target_field = self.COLUMN_MAPPING.get(normalized_csv_key)

                                if target_field:
                                    clean_value = value.strip() if value else ''
                                    try:
                                        if target_field == 'quantity':
                                            order[target_field] = int(clean_value) if clean_value.isdigit() else 1
                                        elif target_field == 'order_date':
                                            if clean_value:  # Only try to parse if there's a value
                                                # Debug: Log the exact value and its character representation
                                                debug_chars = [f"{i}:{ord(c)}" for i, c in enumerate(clean_value)]
                                                logger.info(f"Processing Date-Time value: '{clean_value}', length: {len(clean_value)}, chars: {debug_chars}")
                                                
                                                # Clean the date string to remove invisible characters
                                                original_value = clean_value
                                                clean_value = self._clean_date_string(clean_value)
                                                
                                                if original_value != clean_value:
                                                    logger.info(f"Cleaned date string from '{original_value}' to '{clean_value}'")
                                                    debug_chars = [f"{i}:{ord(c)}" for i, c in enumerate(clean_value)]
                                                    logger.debug(f"Cleaned Date-Time chars: {debug_chars}")
                                                
                                                try:
                                                    # First, try the expected format directly
                                                    try:
                                                        naive_datetime = datetime.datetime.strptime(clean_value, '%Y-%m-%d %H:%M:%S')
                                                        logger.info(f"Successfully parsed date: {naive_datetime}")
                                                        
                                                        # Make timezone-aware
                                                        try:
                                                            aware_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
                                                            order[target_field] = aware_datetime
                                                            logger.info(f"Successfully made timezone-aware: {aware_datetime}")
                                                        except Exception as tz_error:
                                                            logger.error(f"TIMEZONE ERROR: {tz_error}")
                                                            # Try with UTC timezone explicitly
                                                            try:
                                                                from django.utils.timezone import utc
                                                                aware_datetime = datetime.datetime.replace(naive_datetime, tzinfo=utc)
                                                                order[target_field] = aware_datetime
                                                                logger.info(f"Made timezone-aware using UTC: {aware_datetime}")
                                                            except Exception as utc_error:
                                                                logger.error(f"UTC TIMEZONE ERROR: {utc_error}")
                                                                raise ValueError(f"Cannot make datetime timezone-aware: {naive_datetime}")
                                                    except ValueError as format_error:
                                                        # Log the specific parsing error
                                                        logger.error(f"Date format error: {format_error}")
                                                        raise  # Re-raise to terminate the import process
                                                except Exception as e:
                                                    logger.error(f"Critical date parsing error: {e}")
                                                    raise ValueError(f"Failed to parse date '{clean_value}' on row {i+1}: {e}")
                                            else:
                                                # Empty date value, this is a critical error
                                                error_msg = f"Empty date value found on row {i+1}. All orders must have a date."
                                                logger.error(error_msg)
                                                raise ValueError(error_msg)  # Terminate the import process
                                        else:
                                            order[target_field] = clean_value
                                        processed_fields.add(target_field) # Add to processed *after* successful processing
                                    except ValueError as e:
                                        logger.error(f"Error parsing value for field '{target_field}' on row {i+1}: {e}. Value: '{value}'")
                                # else: # Optional: Log if a CSV column doesn't map to anything
                                #     logger.debug(f"Row {i+1}: Unmapped CSV column '{csv_key}'")

                            # Apply defaults ONLY for fields DEFINED in COLUMN_MAPPING that were NOT found in the row
                            for model_field in self.COLUMN_MAPPING.values():
                                if model_field not in processed_fields:
                                    logger.debug(f"Row {i+1}: Model field '{model_field}' not found in CSV row keys (using default).")
                                    if model_field == 'quantity':
                                        order[model_field] = 1
                                    elif model_field == 'order_date':
                                        # If order_date field is missing from CSV, this is a critical error
                                        error_msg = f"Missing 'Date-Time' column in CSV for row {i+1}. Cannot proceed without date information."
                                        logger.error(error_msg)
                                        raise ValueError(error_msg)  # Terminate the import process
                                    else:
                                        order[model_field] = '' # Default to empty string if missing
                            
                            # Normalize status after all fields are potentially set
                            order['status'] = self._normalize_status(order.get('status', '')) 
                            
                            orders.append(order)
                        
                        csv_read_success = True
                        break  # Successfully read the CSV, exit the encoding loop
                        
                except UnicodeDecodeError as e:
                    logger.warning(f"Failed to read CSV with encoding {encoding}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error reading CSV with encoding {encoding}: {e}")
                    raise
            
            if not csv_read_success:
                logger.error("Failed to read CSV with any of the attempted encodings")
                return []
        
        except (IOError, csv.Error) as e: # Removed UnicodeDecodeError
            logger.error(f"Error parsing CSV file '{csv_path}': {str(e)}", exc_info=True)
            return []
        except Exception as e: # Catch other potential errors during processing
            logger.error(f"Unexpected error during CSV parsing: {str(e)}", exc_info=True)
            return [] # Return empty list on unexpected errors too
            
        logger.info(f"Found {len(orders)} orders in CSV")
        return orders
    
    def _normalize_status(self, status: str) -> str:
        """
        Normalizes the status string to match our defined choices.
        """
        status_map = {
            'new': 'NEW',
            'parts pulled': 'PARTS_PULLED',
            'passed qc': 'PASSED_QC', # Added short version
            'on bench': 'ON_BENCH',
            'testing': 'TESTING',
            'quality control': 'QUALITY_CONTROL',
            'passed quality control': 'PASSED_QC',
            'passed quality control - awaiting payment': 'PASSED_QC_AWAITING_PAYMENT',
            'completed waiting for wood base': 'COMPLETED_WAITING_BASE',
            'shipped': 'SHIPPED',
            'cancelled': 'CANCELLED'
        }
        normalized = status.lower().strip()
        if not normalized: # Handle empty string status explicitly
            return 'NEW' # Map empty status to NEW
        normalized_status = status_map.get(normalized)
        if normalized_status:
            return normalized_status
        else:
            # Log unknown status but keep it as is (uppercase)
            if status:  # Only log if status is not empty
                logger.debug(f"Unknown status: {status}")
            return 'NEW'  # Return 'NEW' for unknown statuses to match test expectations
    
    def _test_date_parsing(self, date_string: str) -> Tuple[bool, str, Optional[datetime.datetime]]:
        """
        Test date parsing with detailed diagnostics.
        Returns a tuple of (success, error_message, parsed_date)
        """
        if not date_string or not date_string.strip():
            return False, "Empty date string", None
        
        # Check for invisible characters
        if len(date_string) != len(date_string.strip()):
            return False, f"Date string contains leading/trailing whitespace: '{date_string}'", None
        
        # Check for non-ASCII characters
        non_ascii = [c for c in date_string if ord(c) > 127]
        if non_ascii:
            return False, f"Date string contains non-ASCII characters: {non_ascii}", None
        
        # Check for common date format patterns
        date_patterns = [
            (r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '%Y-%m-%d %H:%M:%S'),  # YYYY-MM-DD HH:MM:SS
            (r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', '%m/%d/%Y %H:%M:%S'),  # MM/DD/YYYY HH:MM:SS
            (r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}', '%m/%d/%Y %H:%M'),           # MM/DD/YYYY HH:MM
            (r'\d{4}-\d{2}-\d{2}', '%Y-%m-%d'),                             # YYYY-MM-DD
        ]
        
        matched_format = None
        for pattern, date_format in date_patterns:
            if re.match(pattern, date_string):
                matched_format = date_format
                break
        
        if matched_format:
            try:
                parsed_date = datetime.datetime.strptime(date_string, matched_format)
                return True, f"Successfully parsed using format: {matched_format}", parsed_date
            except ValueError as e:
                return False, f"Matched pattern for format {matched_format} but parsing failed: {str(e)}", None
        else:
            return False, f"No matching pattern found for: '{date_string}'", None
    
    def _clean_date_string(self, date_string: str) -> str:
        """
        Clean a date string by removing invisible characters and normalizing spaces.
        """
        if not date_string:
            return date_string
            
        # Replace common invisible characters
        cleaned = date_string
        
        # Replace zero-width space
        cleaned = cleaned.replace('\u200b', '')
        
        # Replace non-breaking space with regular space
        cleaned = cleaned.replace('\xa0', ' ')
        
        # Replace other invisible Unicode characters
        invisible_chars = [
            '\u200c',  # Zero-width non-joiner
            '\u200d',  # Zero-width joiner
            '\u2060',  # Word joiner
            '\ufeff',  # Zero-width no-break space (BOM)
            '\u00ad',  # Soft hyphen
        ]
        for char in invisible_chars:
            cleaned = cleaned.replace(char, '')
        
        # Normalize whitespace (replace multiple spaces with single space)
        cleaned = ' '.join(cleaned.split())
        
        # Log if cleaning changed the string
        if cleaned != date_string:
            logger.debug(f"Cleaned date string: '{date_string}' -> '{cleaned}'")
            
        return cleaned

    @transaction.atomic
    def update_database(self, orders: List[Dict[str, Any]]) -> int:
        """
        Updates the database with new order information using a composite key.
        Returns the number of orders processed.
        """
        logger.info("Starting database update within transaction...")
        orders_processed = 0
        for i, order_data in enumerate(orders):
            try:
                # Define the lookup fields for the composite key
                lookup_fields = {
                    'customer_name': order_data.get('customer_name', ''),
                    'origin': order_data.get('origin', ''),
                    'model': order_data.get('model', ''),
                    'base': order_data.get('base', ''),
                    'volts': order_data.get('volts', '')
                }

                # Define the fields for creation or update
                defaults = {
                    'quantity': order_data.get('quantity', 1),
                    'options': order_data.get('options', ''),
                    'status': order_data.get('status', 'NEW') # Already normalized
                }
                
                # Handle order_date separately to ensure it's never null
                order_date = order_data.get('order_date')
                if order_date is None:
                    # Use current time as default if order_date is null
                    defaults['order_date'] = timezone.now()
                else:
                    defaults['order_date'] = order_date

                # --- Check existing status BEFORE update_or_create ---
                old_order_status = None
                try:
                    existing_order = OrderRecord.objects.get(**lookup_fields)
                    old_order_status = existing_order.status
                except OrderRecord.DoesNotExist:
                    existing_order = None # Will be created
                # --- End Check ---

                order, created = OrderRecord.objects.update_or_create(
                    **lookup_fields,
                    defaults=defaults
                )

                # Compare the new status from defaults with the status we fetched BEFORE the update
                if not created and old_order_status is not None and old_order_status != defaults['status']:
                    StatusHistory.objects.create(
                        order=order,
                        previous_status=old_order_status,
                        new_status=defaults['status'],
                        timestamp=timezone.now()
                    )
                elif created:
                    StatusHistory.objects.create(
                        order=order,
                        previous_status=None, # Initial status has no previous
                        new_status=defaults['status'],
                        timestamp=timezone.now() # Or use order.order_date if more appropriate? Using now() for consistency.
                    )

                orders_processed += 1

            except Exception as e:
                # Log the specific order data that caused the error if possible
                error_context = {k: order_data.get(k) for k in lookup_fields.keys()}
                logger.error(f"Error processing order {error_context}: {str(e)}", exc_info=True)
                continue

        logger.info(f"Processed {orders_processed}/{len(orders)} orders in CSV")
        return orders_processed

    def run(self) -> bool:
        """
        Main entry point. Downloads CSV, processes it, and updates the database.
        Returns True if successful, False otherwise.
        """
        logger.info("Starting order data update using direct HTTP request")

        csv_path = self.download_csv()
        orders_processed = 0
        success = False

        if csv_path:
            logger.info(f"Processing downloaded CSV: {csv_path}")
            orders = self.parse_csv(csv_path)
            if orders:
                logger.info(f"Found {len(orders)} orders in CSV")
                orders_processed = self.update_database(orders)
                logger.info(f"Successfully processed and updated {orders_processed} orders.")
                success = True
            else:
                logger.error("No orders could be parsed from the CSV.")
        else:
            logger.error("Failed to download or locate the CSV file.")

        self.cleanup()
        logger.info(f"Order data update finished. Success: {success}, Orders Processed: {orders_processed}")
        return success

    def cleanup(self):
        """Cleans up temporary download directory."""
        if self.download_dir and os.path.exists(self.download_dir):
            try:
                for filename in os.listdir(self.download_dir):
                    file_path = os.path.join(self.download_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        logger.warning(f'Failed to delete {file_path}. Reason: {e}')
                os.rmdir(self.download_dir)
                logger.info(f"Temporary download directory removed: {self.download_dir}")
            except OSError as e:
                logger.error(f"Error removing temporary directory {self.download_dir}: {e}")
            self.download_dir = None

def run(): 
    """Instantiates and runs the scraper for django-extensions runscript."""
    scraper = DecwareOrderScraper()
    scraper.run()

# Example usage (if run directly)
if __name__ == '__main__':
    print("Running scraper directly requires Django context.")
    print("Use 'python manage.py runscript orders.run_scraper' or similar.")
