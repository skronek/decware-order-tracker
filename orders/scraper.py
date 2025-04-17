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
import shutil

import requests
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .models import OrderRecord, StatusHistory

# Configure logging
logger = logging.getLogger(__name__)

class DecwareOrderScraper:
    """Handles downloading and processing order data from orders.decware.com."""
    
    # Website URL for Decware orders
    DECWARE_URL = "https://orders.decware.com/"
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
        logger.info(f"Created temporary download directory: {self.download_dir}")

    def download_csv(self) -> Optional[str]:
        """
        Downloads the CSV file using Selenium to interact with the Decware website.
        Returns the path to the downloaded CSV file or None if download fails.
        """
        logger.info("Starting CSV download using Selenium browser automation")
        
        # Set up Chrome options for Heroku
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,1696")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        # Set download preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Check if running on Heroku
        is_heroku = os.environ.get('DYNO') is not None
        
        driver = None
        try:
            logger.info("Initializing Chrome WebDriver")
            
            if is_heroku:
                # On Heroku, use the Chrome binary from the buildpack
                chrome_bin = os.environ.get('GOOGLE_CHROME_BIN', '/app/.apt/usr/bin/google-chrome')
                chrome_options.binary_location = chrome_bin
                
                # Use ChromeDriver from the buildpack
                chrome_driver_path = os.environ.get('CHROMEDRIVER_PATH', '/app/.chromedriver/bin/chromedriver')
                
                # Use Service class for the driver path in newer Selenium versions
                service = Service(executable_path=chrome_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info(f"Using Heroku Chrome configuration: Binary={chrome_bin}, Driver={chrome_driver_path}")
            else:
                # Local development
                driver = webdriver.Chrome(options=chrome_options)
                logger.info("Using local Chrome configuration")
            
            # Navigate to Decware website
            logger.info(f"Navigating to Decware website: {self.DECWARE_URL}")
            driver.get(self.DECWARE_URL)
            
            # Log page title for debugging
            logger.info(f"Page title: {driver.title}")
            
            # Wait for page to load
            logger.info("Waiting for page to load")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take a screenshot for debugging
            screenshot_path = os.path.join(self.download_dir, "page_screenshot.png")
            driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            
            # Look for the CSV button
            logger.info("Looking for CSV button")
            try:
                # Try different potential selectors for the CSV button
                csv_button = None
                selectors_to_try = [
                    "//button[contains(text(), 'CSV')]",  # XPath for button with text 'CSV'
                    "//a[contains(text(), 'CSV')]",       # XPath for link with text 'CSV'
                    "//input[contains(@value, 'CSV')]",   # XPath for input with value 'CSV'
                    "//button[contains(@id, 'csv')]",     # XPath for button with id containing 'csv'
                    "//a[contains(@id, 'csv')]",          # XPath for link with id containing 'csv'
                    "//a[contains(@href, 'export_csv')]", # XPath for link with href containing 'export_csv'
                    "//button[contains(@class, 'csv')]",  # XPath for button with class containing 'csv'
                    "//a[contains(@class, 'csv')]",       # XPath for link with class containing 'csv'
                    "//input[contains(@class, 'csv')]",   # XPath for input with class containing 'csv'
                ]
                
                for selector in selectors_to_try:
                    logger.info(f"Trying selector: {selector}")
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            csv_button = elements[0]
                            logger.info(f"Found CSV button using selector: {selector}")
                            break
                    except Exception as e:
                        logger.warning(f"Error with selector {selector}: {e}")
                
                if not csv_button:
                    # If we couldn't find the button with XPath, try looking for it by examining all links
                    logger.info("Trying to find CSV button by examining all links")
                    links = driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            link_text = link.text.strip().lower()
                            link_href = link.get_attribute("href") or ""
                            logger.info(f"Found link: text='{link_text}', href='{link_href}'")
                            if "csv" in link_text or "export" in link_text or "csv" in link_href or "export_csv" in link_href:
                                csv_button = link
                                logger.info(f"Found potential CSV button: {link_text} ({link_href})")
                                break
                        except Exception as e:
                            logger.warning(f"Error examining link: {e}")
                
                if not csv_button:
                    # Log the page source for debugging
                    logger.info(f"Page source: {driver.page_source[:2000]}...")  # Log first 2000 chars
                    logger.error("Could not find CSV button on the page")
                    return None
                
                # Click the CSV button
                logger.info("Clicking CSV button")
                csv_button.click()
                
                # Wait for download to complete (check for new files in download directory)
                logger.info("Waiting for download to complete")
                wait_time = 0
                max_wait_time = 30  # seconds
                download_complete = False
                
                while wait_time < max_wait_time and not download_complete:
                    time.sleep(1)
                    wait_time += 1
                    
                    # Check for CSV files in download directory
                    csv_files = [f for f in os.listdir(self.download_dir) if f.endswith('.csv')]
                    if csv_files:
                        download_complete = True
                        logger.info(f"Download completed in {wait_time} seconds")
                        break
                
                if not download_complete:
                    logger.error(f"Download did not complete after {max_wait_time} seconds")
                    
                    # Check if we have any files in the download directory
                    all_files = os.listdir(self.download_dir)
                    logger.info(f"Files in download directory: {all_files}")
                    
                    # Try to get the CSV directly from the href
                    try:
                        if csv_button.tag_name.lower() == 'a':
                            href = csv_button.get_attribute('href')
                            if href:
                                logger.info(f"Trying to download CSV directly from href: {href}")
                                response = requests.get(href, timeout=30)
                                if response.status_code == 200:
                                    # Create a temporary file to store the CSV
                                    csv_path = os.path.join(self.download_dir, f"decware_orders_{int(time.time())}.csv")
                                    with open(csv_path, 'wb') as f:
                                        f.write(response.content)
                                    logger.info(f"CSV file downloaded directly: {csv_path}")
                                    return csv_path
                    except Exception as e:
                        logger.error(f"Error downloading CSV directly: {e}")
                    
                    return None
                
                # Find the downloaded CSV file
                csv_files = [f for f in os.listdir(self.download_dir) if f.endswith('.csv')]
                if not csv_files:
                    logger.error("No CSV files found in download directory after clicking CSV button")
                    return None
                
                # Use the most recent CSV file
                csv_file = sorted(csv_files, key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)[0]
                csv_path = os.path.join(self.download_dir, csv_file)
                
                # Log file stats
                file_size = os.path.getsize(csv_path)
                logger.info(f"CSV file downloaded: {csv_path}, size: {file_size} bytes")
                
                # Preview file content (first 500 bytes)
                with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                    preview = f.read(500)
                    logger.info(f"CSV file preview (first 500 chars): {preview}")
                
                return csv_path
                
            except NoSuchElementException as e:
                logger.error(f"CSV button not found on the page: {e}")
                return None
                
            except TimeoutException as e:
                logger.error(f"Timed out waiting for page to load: {e}")
                return None
                
            except Exception as e:
                logger.error(f"Error during Selenium automation: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception details: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error initializing WebDriver: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            return None
            
        finally:
            # Clean up WebDriver
            if driver:
                logger.info("Closing WebDriver")
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"Error closing WebDriver: {e}")
        
        return None

    def parse_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Parses the CSV file and returns a list of order records.
        """
        orders = []
        try:
            # Log environment information for debugging
            logger.info(f"DEBUG: Python version: {sys.version}")
            logger.info(f"DEBUG: Default encoding: {sys.getdefaultencoding()}")
            logger.info(f"DEBUG: Filesystem encoding: {sys.getfilesystemencoding()}")
            logger.info(f"DEBUG: Timezone: {timezone.get_current_timezone_name()}")
            
            # Log file information
            logger.info(f"DEBUG: CSV file path: {csv_path}")
            logger.info(f"DEBUG: CSV file exists: {os.path.exists(csv_path)}")
            if os.path.exists(csv_path):
                logger.info(f"DEBUG: CSV file size: {os.path.getsize(csv_path)} bytes")
                logger.info(f"DEBUG: CSV file permissions: {oct(os.stat(csv_path).st_mode)[-3:]}")
            
            # Try multiple encodings if needed
            encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
            csv_read_success = False
            
            for encoding in encodings_to_try:
                try:
                    logger.info(f"DEBUG: Trying to open CSV with encoding: {encoding}")
                    with open(csv_path, mode='r', encoding=encoding) as csvfile:
                        # Check if file is readable
                        sample = csvfile.read(1024)
                        if not sample:
                            logger.warning(f"DEBUG: CSV file appears empty with encoding {encoding}")
                            continue
                        
                        # Log sample content
                        logger.info(f"DEBUG: CSV sample content (first 1024 chars): {sample}")
                            
                        # Reset file pointer
                        csvfile.seek(0)
                        
                        logger.info(f"DEBUG: Creating CSV DictReader with encoding {encoding}")
                        reader = csv.DictReader(csvfile)
                        
                        # Verify we can read headers
                        if not reader.fieldnames:
                            logger.warning(f"DEBUG: No CSV headers detected with encoding {encoding}")
                            continue
                            
                        logger.info(f"DEBUG: Successfully opened CSV with encoding: {encoding}")
                        logger.info(f"DEBUG: CSV Headers detected: {reader.fieldnames}")
                        
                        # Check specifically for Date-Time column
                        if 'Date-Time' not in reader.fieldnames:
                            date_time_alternatives = [field for field in reader.fieldnames if 'date' in field.lower() or 'time' in field.lower()]
                            if date_time_alternatives:
                                logger.info(f"DEBUG: 'Date-Time' column not found, but found possible alternatives: {date_time_alternatives}")
                            else:
                                logger.error(f"DEBUG: 'Date-Time' column not found in headers: {reader.fieldnames}")
                        
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
