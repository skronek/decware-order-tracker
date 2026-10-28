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
import shutil

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .models import OrderRecord, StatusHistory

# Status changes are only counted as observed if the previous successful run was this recent
MAX_OBSERVED_RUN_GAP = datetime.timedelta(days=3)
# Don't mark orders removed unless the CSV contained at least this share of active orders
MIN_SEEN_FRACTION_FOR_REMOVALS = 0.5
# Fields that together identify an order (Decware's CSV has no order ID)
KEY_FIELDS = ('customer_name', 'origin', 'model', 'base', 'volts')

# Configure logging
logger = logging.getLogger(__name__)

class DecwareOrderScraper:
    """Handles downloading and processing order data from orders.decware.com."""

    # Website URL for Decware orders
    DECWARE_URL = "https://orders.decware.com/"
    DOWNLOAD_TIMEOUT_SECONDS = 30
    ENCODINGS = ['utf-8-sig', 'latin-1']  # latin-1 decodes any byte sequence

    # Mapping from CSV Column Header (surrounding whitespace ignored) to OrderRecord model field name
    COLUMN_MAPPING = {
        # CSV Header        : Model Field Name
        'For'              : 'customer_name',
        'From'             : 'origin',
        'Qty'              : 'quantity',
        'MODEL'            : 'model',
        'Base'             : 'base',
        'VOLTS'            : 'volts',
        'Options'          : 'options',
        'Status'           : 'status',
        'Date-Time'        : 'order_date',
    }
    REQUIRED_FIELDS = {'customer_name', 'model', 'status', 'order_date'}

    # Decware's status text (lowercased) to OrderRecord.STATUS_CHOICES
    STATUS_MAP = {
        '': 'NEW',  # New orders have no status yet
        'new': 'NEW',
        'parts pulled': 'PARTS_PULLED',
        'on bench': 'ON_BENCH',
        'testing': 'TESTING',
        'quality control': 'QUALITY_CONTROL',
        'passed qc': 'PASSED_QC',
        'passed quality control': 'PASSED_QC',
        'passed quality control - awaiting payment': 'PASSED_QC_AWAITING_PAYMENT',
        'completed waiting for wood base': 'COMPLETED_WAITING_BASE',
    }

    def __init__(self):
        self.download_dir = None  # Created by download_csv, removed by cleanup

    def _init_driver(self):
        """
        Initialize and configure the Chrome WebDriver.
        Returns a configured WebDriver instance, or None if Chrome can't be started.
        """
        if getattr(settings, 'TESTING', False):
            raise RuntimeError("Refusing to launch Chrome in tests; patch _init_driver instead")

        # Set up Chrome options for Heroku
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,1696")

        # Set download preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            if os.environ.get('DYNO') is not None:
                # The Chrome for Testing buildpack puts a version-matched `chrome` and
                # `chromedriver` on PATH. Both must come from the buildpack: if either is
                # missing, Selenium Manager downloads the latest one at runtime, which
                # won't match the other.
                chrome_bin = os.environ.get('GOOGLE_CHROME_BIN') or shutil.which('chrome')
                chrome_driver_path = os.environ.get('CHROMEDRIVER_PATH') or shutil.which('chromedriver')
                logger.info(f"Chrome binary: {chrome_bin}, ChromeDriver: {chrome_driver_path}")

                if not chrome_bin or not chrome_driver_path:
                    logger.error("Chrome or ChromeDriver not found on PATH; is the chrome-for-testing buildpack installed?")
                    return None

                chrome_options.binary_location = chrome_bin
                service = Service(executable_path=chrome_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info(f"Using Chrome {driver.capabilities.get('browserVersion')}")
            else:
                # Local development
                driver = webdriver.Chrome(options=chrome_options)
                logger.info("Using local Chrome configuration")

            return driver

        except Exception as e:
            logger.error(f"Error initializing WebDriver ({type(e).__name__}): {e}")
            return None

    def _csv_files(self):
        return [f for f in os.listdir(self.download_dir) if f.endswith('.csv')]

    def download_csv(self) -> Optional[str]:
        """
        Downloads the CSV file using Selenium to interact with the Decware website.
        Returns the path to the downloaded CSV file or None if download fails.
        """
        logger.info("Starting CSV download using Selenium browser automation")
        if self.download_dir is None:
            self.download_dir = tempfile.mkdtemp()

        driver = self._init_driver()
        if driver is None:
            logger.error("Failed to initialize WebDriver")
            return None

        try:
            logger.info(f"Navigating to Decware website: {self.DECWARE_URL}")
            driver.get(self.DECWARE_URL)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info(f"Page loaded: {driver.title}")

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
                for link in driver.find_elements(By.TAG_NAME, "a"):
                    try:
                        link_text = link.text.strip().lower()
                        link_href = link.get_attribute("href") or ""
                        if "csv" in link_text or "export" in link_text or "csv" in link_href or "export_csv" in link_href:
                            csv_button = link
                            logger.info(f"Found potential CSV button: {link_text} ({link_href})")
                            break
                    except Exception as e:
                        logger.warning(f"Error examining link: {e}")

            if not csv_button:
                logger.error(f"Could not find CSV button on the page. Page source: {driver.page_source[:2000]}...")
                return None

            logger.info("Clicking CSV button")
            csv_button.click()

            # Wait for the download to appear in the download directory
            for waited in range(1, self.DOWNLOAD_TIMEOUT_SECONDS + 1):
                time.sleep(1)
                if self._csv_files():
                    logger.info(f"Download completed in {waited} seconds")
                    break
            else:
                logger.error(f"Download did not complete after {self.DOWNLOAD_TIMEOUT_SECONDS} seconds")
                return self._download_from_href(csv_button)

            # Use the most recent CSV file
            csv_file = max(self._csv_files(), key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)))
            csv_path = os.path.join(self.download_dir, csv_file)
            logger.info(f"CSV file downloaded: {csv_path}, size: {os.path.getsize(csv_path)} bytes")
            return csv_path

        except NoSuchElementException as e:
            logger.error(f"CSV button not found on the page: {e}")
            return None

        except TimeoutException as e:
            logger.error(f"Timed out waiting for page to load: {e}")
            return None

        except Exception as e:
            logger.error(f"Error during Selenium automation ({type(e).__name__}): {e}")
            return None

        finally:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")

    def _download_from_href(self, csv_button) -> Optional[str]:
        """Fallback when clicking didn't produce a file: fetch the CSV link's href directly."""
        try:
            if csv_button.tag_name.lower() != 'a':
                return None
            href = csv_button.get_attribute('href')
            if not href:
                return None
            logger.info(f"Trying to download CSV directly from href: {href}")
            response = requests.get(href, timeout=30)
            if response.status_code != 200:
                logger.error(f"Direct CSV download returned HTTP {response.status_code}")
                return None
            csv_path = os.path.join(self.download_dir, f"decware_orders_{int(time.time())}.csv")
            with open(csv_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"CSV file downloaded directly: {csv_path}")
            return csv_path
        except Exception as e:
            logger.error(f"Error downloading CSV directly: {e}")
            return None

    def parse_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Parse the CSV file and return a list of order dictionaries with normalized field names.
        """
        logger.info(f"Parsing CSV file: {csv_path}")
        for encoding in self.ENCODINGS:
            try:
                with open(csv_path, 'r', encoding=encoding, newline='') as csvfile:
                    return self._parse_rows(csv.DictReader(csvfile))
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode CSV with {encoding} encoding, trying next encoding")
            except (OSError, csv.Error) as e:
                logger.error(f"Error parsing CSV: {e}")
                return []
        return []

    def _parse_rows(self, reader: csv.DictReader) -> List[Dict[str, Any]]:
        field_names = reader.fieldnames
        if not field_names:
            logger.error("CSV file has no headers")
            return []
        logger.info(f"CSV headers: {field_names}")

        field_mapping = self._create_field_mapping(field_names)
        if not field_mapping:
            return []

        orders = []
        for row in reader:
            # Skip empty rows
            if not any(row.values()):
                continue
            try:
                order = self._process_csv_row(row, field_mapping)
            except Exception as e:
                logger.error(f"Error processing CSV row {row}: {e}")
                continue
            if order:
                orders.append(order)

        logger.info(f"Successfully parsed {len(orders)} orders from CSV")
        return orders

    def _normalize_status(self, status: str) -> Optional[str]:
        """
        Maps Decware's status text to one of OrderRecord.STATUS_CHOICES.
        Returns None for statuses we don't recognize.
        """
        return self.STATUS_MAP.get(status.lower().strip())

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

    def _create_field_mapping(self, field_names: List[str]) -> Dict[str, str]:
        """
        Create a mapping from CSV field names to model field names.
        Returns {} if a required column is missing.
        """
        field_mapping = {}
        for csv_field in field_names:
            if csv_field is None:
                continue
            normalized_field = csv_field.strip()
            if normalized_field in self.COLUMN_MAPPING:
                field_mapping[normalized_field] = self.COLUMN_MAPPING[normalized_field]

        missing_fields = self.REQUIRED_FIELDS - set(field_mapping.values())
        if missing_fields:
            logger.error(f"Missing required fields in CSV: {missing_fields}. Available fields: {field_names}")
            return {}
        return field_mapping

    def _process_csv_row(self, row: Dict[str, str], field_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Process a CSV row and return a normalized order dictionary, or None if the row
        can't be used. An unrecognized status is returned as None so update_database
        keeps the order's current status.
        """
        order = {}
        for csv_key, value in row.items():
            if csv_key is None:  # Extra values beyond the header row
                continue
            target_field = field_mapping.get(csv_key.strip())
            if not target_field:
                continue
            clean_value = value.strip() if value else ''
            if target_field == 'quantity':
                order[target_field] = int(clean_value) if clean_value.isdigit() else 1
            elif target_field == 'order_date':
                clean_value = self._clean_date_string(clean_value)
                try:
                    naive_datetime = datetime.datetime.strptime(clean_value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    logger.error(f"Skipping row with invalid date {clean_value!r}: {row}")
                    return None
                order[target_field] = timezone.make_aware(naive_datetime)
            else:
                order[target_field] = clean_value

        raw_status = order['status']
        order['status'] = self._normalize_status(raw_status)
        if order['status'] is None:
            logger.warning(f"Unknown status {raw_status!r}; keeping the order's current status: {row}")
        return order

    @transaction.atomic
    def update_database(self, orders: List[Dict[str, Any]]) -> int:
        """
        Updates the database with new order information using a composite key.
        Returns the number of orders processed.
        """
        logger.info("Starting database update within transaction...")
        run_time = timezone.now()
        # A status change is only timestamped accurately if the previous run was recent;
        # after missed runs we only know it happened sometime during the gap.
        previous_run = OrderRecord.objects.aggregate(Max('last_seen_at'))['last_seen_at__max']
        changes_observed = previous_run is not None and run_time - previous_run <= MAX_OBSERVED_RUN_GAP
        if not changes_observed:
            logger.warning(f"Previous successful run was {previous_run}; status changes this run are marked unobserved")

        orders_processed = 0
        seen_ids = set()
        seen_keys = set()
        for order_data in orders:
            lookup_fields = {field: order_data.get(field, '') for field in KEY_FIELDS}
            key = tuple(lookup_fields.values())
            if key in seen_keys:
                # Two rows with the same key would overwrite each other's status
                logger.warning(f"Skipping duplicate order in CSV (keeping the first): {lookup_fields}")
                continue
            seen_keys.add(key)

            try:
                status = order_data.get('status')
                defaults = {
                    'quantity': order_data.get('quantity', 1),
                    'options': order_data.get('options', ''),
                    'order_date': order_data['order_date'],
                    'last_seen_at': run_time,
                    'removed_at': None,  # Back on the list if it had dropped off
                }
                if status is not None:  # None: unrecognized status, keep the current one
                    defaults['status'] = status

                # Savepoint per order, so one failing order doesn't abort the whole transaction
                with transaction.atomic():
                    try:
                        order = OrderRecord.objects.get(**lookup_fields)
                    except OrderRecord.DoesNotExist:
                        if status is None:
                            logger.warning(f"Not creating order with unknown status: {lookup_fields}")
                            continue
                        order = OrderRecord.objects.create(**lookup_fields, **defaults)
                        StatusHistory.objects.create(
                            order=order,
                            previous_status=None,  # Initial status has no previous
                            new_status=status,
                            timestamp=run_time,
                            is_observed=False,  # We don't know how long it was already in this status
                        )
                    else:
                        old_status = order.status
                        for field, value in defaults.items():
                            setattr(order, field, value)
                        order.save()
                        if status is not None and status != old_status:
                            StatusHistory.objects.create(
                                order=order,
                                previous_status=old_status,
                                new_status=status,
                                timestamp=run_time,
                                is_observed=changes_observed,
                            )
            except Exception as e:
                logger.error(f"Error processing order {lookup_fields}: {e}", exc_info=True)
                continue

            seen_ids.add(order.pk)
            orders_processed += 1

        logger.info(f"Processed {orders_processed}/{len(orders)} orders in CSV")
        self._mark_removed_orders(seen_ids, run_time)
        return orders_processed

    def _mark_removed_orders(self, seen_ids, run_time):
        """
        Marks orders that are no longer in the CSV as removed (finished).
        Skipped when this run saw too few of the active orders, since that points
        to a partial download rather than a mass completion.
        """
        active = OrderRecord.objects.filter(removed_at__isnull=True)
        active_count = active.count()
        if active_count and len(seen_ids) < active_count * MIN_SEEN_FRACTION_FOR_REMOVALS:
            logger.error(
                f"Only {len(seen_ids)} of {active_count} active orders were in the CSV; "
                "not marking any orders as removed"
            )
            return 0
        removed = active.exclude(pk__in=seen_ids).update(removed_at=run_time)
        logger.info(f"Marked {removed} orders no longer in the CSV as removed")
        return removed

    def run(self) -> bool:
        """
        Main entry point. Downloads CSV, processes it, and updates the database.
        Returns True if successful, False otherwise.
        """
        logger.info("Starting order data update")
        try:
            csv_path = self.download_csv()
            if not csv_path:
                logger.error("Failed to download or locate the CSV file.")
                return False
            orders = self.parse_csv(csv_path)
            if not orders:
                logger.error("No orders could be parsed from the CSV.")
                return False
            orders_processed = self.update_database(orders)
            logger.info(f"Successfully processed and updated {orders_processed} orders.")
            return True
        finally:
            self.cleanup()

    def cleanup(self):
        """Removes the temporary download directory."""
        if self.download_dir:
            shutil.rmtree(self.download_dir, ignore_errors=True)
            self.download_dir = None
