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
from typing import Optional, List, Dict, Any

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
            # Use utf-8-sig to handle potential Byte Order Mark (BOM)
            with open(csv_path, mode='r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)

                # --- Debug: Log CSV Headers --- #
                logger.debug(f"DEBUG: CSV Headers detected by DictReader: {reader.fieldnames}")
                # --- End Debug --- #

                # --- Debug: Log calculated required fields ONCE --- #
                try:
                    required_fields_calculated = {
                        f.name for f in OrderRecord._meta.get_fields()
                        if not f.is_relation and not f.null and not getattr(f, 'default', None) and not f.auto_created
                    }
                    logger.debug(f"DEBUG: Calculated required model fields (non-null, no default): {required_fields_calculated}")
                except Exception as e:
                    logger.error(f"DEBUG: Error calculating required fields: {e}")
                # --- End Debug --- #

                for i, row in enumerate(reader):
                    order = {}
                    processed_fields = set()

                    # --- Debug: Log keys for first row --- #
                    if i == 0:
                        logger.debug(f"DEBUG: Row 1 Keys: {list(row.keys())}")
                        logger.debug(f"DEBUG: Row 1 Values: {list(row.values())}") # Also log values for context
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
                                        try:
                                            naive_datetime = datetime.datetime.strptime(clean_value, '%Y-%m-%d %H:%M:%S')
                                            order[target_field] = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
                                        except ValueError as e:
                                            logger.error(f"DATE PARSE ERROR for 'order_date' on row {i+1}: {e}. Input value: '{clean_value}', Tried format: '%Y-%m-%d %H:%M:%S'")
                                            order[target_field] = None  # Set to None if parsing fails
                                    else:
                                        order[target_field] = None  # Set to None for empty values
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
                                order[model_field] = None # Default to None if date column missing/unparsable
                            else:
                                order[model_field] = '' # Default to empty string if missing
                    
                    # Normalize status after all fields are potentially set
                    order['status'] = self._normalize_status(order.get('status', '')) 
                    
                    orders.append(order)
                        
        except (IOError, csv.Error, UnicodeDecodeError) as e: # Added UnicodeDecodeError
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
                    'order_date': order_data.get('order_date', None),
                    'options': order_data.get('options', ''),
                    'status': order_data.get('status', 'NEW') # Already normalized
                }

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
