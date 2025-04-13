"""
Unit tests for the CSV parsing and database update logic in orders/scraper.py.
"""

import csv
import io
import datetime
import time
from unittest.mock import patch, mock_open, MagicMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from django.test import TestCase
from django.utils import timezone

from .models import OrderRecord, StatusHistory
from .scraper import DecwareOrderScraper
import os, tempfile, shutil

# Test cases will go here

class ScraperParseCsvTests(TestCase):
    """Tests the parse_csv method of the DecwareOrderScraper."""

    def setUp(self):
        """Initial setup for scraper tests."""
        # Instantiate the scraper - we won't use its driver or download methods
        # Patching _init_driver to avoid actual Selenium setup
        with patch('orders.scraper.DecwareOrderScraper._init_driver', return_value=None):
            self.scraper = DecwareOrderScraper()
        # Prevent cleanup from running and potentially deleting mock dirs if needed later
        self.scraper.cleanup = lambda: None

    def test_parse_valid_csv(self):
        """Test parsing a standard, valid CSV."""
        csv_content = (
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\n'
            'User1,Web,1,M1,B1,V1,O1,New,"2023-01-15 10:00:00"\n'
            'User2,Mail,2,M2,B2,V2,O2,Shipped,"2023-01-16 11:30:00"'
        )
        mock_file = io.StringIO(csv_content)

        # Mock open to return our StringIO object
        with patch('builtins.open', return_value=mock_file):
            parsed_data = self.scraper.parse_csv('dummy_path.csv')

        self.assertEqual(len(parsed_data), 2)

        # Check Order 1
        order1 = parsed_data[0]
        self.assertEqual(order1['customer_name'], 'User1')
        self.assertEqual(order1['origin'], 'Web')
        self.assertEqual(order1['quantity'], 1)
        self.assertEqual(order1['model'], 'M1')
        self.assertEqual(order1['base'], 'B1')
        self.assertEqual(order1['volts'], 'V1')
        self.assertEqual(order1['options'], 'O1')
        self.assertEqual(order1['status'], 'NEW') # Normalized
        expected_dt1 = timezone.make_aware(datetime.datetime(2023, 1, 15, 10, 0, 0))
        self.assertEqual(order1['order_date'], expected_dt1)

        # Check Order 2
        order2 = parsed_data[1]
        self.assertEqual(order2['customer_name'], 'User2')
        self.assertEqual(order2['quantity'], 2)
        self.assertEqual(order2['status'], 'SHIPPED') # Normalized
        expected_dt2 = timezone.make_aware(datetime.datetime(2023, 1, 16, 11, 30, 0))
        self.assertEqual(order2['order_date'], expected_dt2)

    def test_parse_csv_with_missing_columns(self):
        """Test parsing a CSV where some expected columns are missing in data rows."""
        csv_content = (
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\n'
            'User1,Web,1,M1,,,OptionA,,"2023-01-01 00:00:00"\n'
            'User2,Mail,2,M2,Wood,120V,OptionB,Shipped,'
        )
        mock_file = io.StringIO(csv_content)

        with patch('builtins.open', return_value=mock_file):
            parsed_data = self.scraper.parse_csv('dummy_path.csv')

        self.assertEqual(len(parsed_data), 2)
        order = parsed_data[0]
        self.assertEqual(order['customer_name'], 'User1')
        self.assertEqual(order['model'], 'M1')
        self.assertEqual(order['status'], 'NEW')
        expected_dt = timezone.make_aware(datetime.datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(order['order_date'], expected_dt)
        # Check defaults for missing mapped fields
        self.assertEqual(order['origin'], 'Web') # Default 'Web'
        self.assertEqual(order['quantity'], 1) # Default 1
        self.assertEqual(order['base'], '')   # Default empty string
        self.assertEqual(order['volts'], '')  # Default empty string
        self.assertEqual(order['options'], 'OptionA') # Should be 'OptionA' based on data

        # Check User 2 status in missing_columns (should now be SHIPPED)
        order2 = parsed_data[1]
        self.assertEqual(order2['status'], 'SHIPPED') # Assert SHIPPED

    def test_parse_csv_with_extra_columns(self):
        """Test parsing a CSV with extra columns not in mapping."""
        csv_content = (
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time,ExtraCol1,ExtraCol2\n'
            'User1,Web,1,M1,B1,V1,O1,New,"2023-01-15 10:00:00",extra1a,extra2a\n'
            'User2,Mail,2,M2,B2,V2,O2,Shipped,"2023-01-16 11:30:00",extra1b,extra2b'
        )
        mock_file = io.StringIO(csv_content)

        with patch('builtins.open', return_value=mock_file):
            parsed_data = self.scraper.parse_csv('dummy_path.csv')

        self.assertEqual(len(parsed_data), 2)
        order = parsed_data[0]
        self.assertEqual(order['customer_name'], 'User1')
        self.assertEqual(order['model'], 'M1')
        self.assertEqual(order['status'], 'NEW')
        # Ensure extra columns are not present
        self.assertNotIn('ExtraCol1', order)
        self.assertNotIn('ExtraCol2', order)

    def test_parse_csv_status_normalization(self):
        """Test various status strings are correctly normalized."""
        csv_content = (
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\n'
            'User1,Web,1,M1,B1,V1,O1,new,"2023-01-01 00:00:00"\n'
            'User2,Web,1,M2,B2,V2,O2,PARTS PULLED,"2023-01-01 00:00:00"\n'
            'User3,Web,1,M3,B3,V3,O3,On Bench,"2023-01-01 00:00:00"\n'
            'User4,Web,1,M4,B4,V4,O4, passed qc ,"2023-01-01 00:00:00"\n'
            'User5,Web,1,M5,B5,V5,O5,InvalidStatus,"2023-01-01 00:00:00"\n'
            'User6,Web,1,M6,B6,V6,O6,,,"2023-01-17 12:00:00"'
        )
        mock_file = io.StringIO(csv_content)

        with patch('builtins.open', return_value=mock_file):
            parsed_data = self.scraper.parse_csv('dummy_path.csv')

        self.assertEqual(len(parsed_data), 6)
        self.assertEqual(parsed_data[0]['status'], 'NEW')
        self.assertEqual(parsed_data[1]['status'], 'PARTS_PULLED')
        self.assertEqual(parsed_data[2]['status'], 'ON_BENCH')
        self.assertEqual(parsed_data[3]['status'], 'PASSED_QC')
        self.assertEqual(parsed_data[4]['status'], 'NEW') # Unknown defaults to NEW
        self.assertEqual(parsed_data[5]['status'], 'NEW') # Empty defaults to NEW

    def test_parse_csv_bad_data_types(self):
        """Test handling of incorrect data types (e.g., non-int Qty, bad date)."""
        csv_content = (
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\n'
            'User1,Web,ABC,M1,B1,V1,O1,New,"2023-01-15 10:00:00"\n'
            'User2,Web,1,M2,B2,V2,O2,New,"NOT A DATE"'
        )
        mock_file = io.StringIO(csv_content)

        with patch('builtins.open', return_value=mock_file), \
             patch('orders.scraper.logger.error') as mock_logger_error:
            parsed_data = self.scraper.parse_csv('dummy_path.csv')

        self.assertEqual(len(parsed_data), 2)
        # Bad Qty should default to 1
        self.assertEqual(parsed_data[0]['quantity'], 1)
        # Bad Date should default to None and log an error
        self.assertIsNone(parsed_data[1]['order_date'])
        mock_logger_error.assert_called()
        # Check if the specific date parse error was logged
        call_args_list = mock_logger_error.call_args_list
        date_error_logged = any(
            'DATE PARSE ERROR' in call[0][0] and 'NOT A DATE' in call[0][0] 
            for call in call_args_list
        )
        self.assertTrue(date_error_logged, "Expected date parsing error not logged.")

    def test_parse_csv_with_bom(self):
        """Test parsing CSV with a UTF-8 Byte Order Mark (BOM)."""
        # The scraper's open(..., encoding='utf-8-sig') handles the BOM.
        # We provide the decoded string content directly to the mock.
        csv_data_decoded = (
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\n'
            'User1,Web,1,MODELA,BaseA,120V,OptionA,New,"2024-01-15 10:00:00"'
        )
        mock_file = io.StringIO(csv_data_decoded)

        # Patch builtins.open to return our StringIO object
        with patch('builtins.open', return_value=mock_file, create=True):
            with patch('orders.scraper.DecwareOrderScraper._init_driver', return_value=None):
                scraper_instance = DecwareOrderScraper()
                scraper_instance.cleanup = lambda: None
                # The scraper will call open('dummy_path.csv', mode='r', encoding='utf-8-sig')
                # Our patched open returns mock_file, which contains the decoded string.
                # The 'utf-8-sig' encoding on the scraper side will handle the StringIO content correctly.
                parsed_data = scraper_instance.parse_csv('dummy_path.csv')

        self.assertEqual(len(parsed_data), 1)
        self.assertEqual(parsed_data[0]['customer_name'], 'User1')
        self.assertEqual(parsed_data[0]['model'], 'MODELA')
        self.assertEqual(parsed_data[0]['status'], 'NEW')

    def test_parse_empty_csv(self):
        """Test parsing an empty CSV file (only headers)."""
        csv_content = 'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\n'
        mock_file = io.StringIO(csv_content)

        with patch('builtins.open', return_value=mock_file):
            parsed_data = self.scraper.parse_csv('dummy_path.csv')

        self.assertEqual(len(parsed_data), 0)

    def test_parse_csv_io_error(self):
        """Test handling of IOError when opening the CSV."""
        with patch('builtins.open', side_effect=IOError("File not found")) as mock_file_open, \
             patch('orders.scraper.logger.error') as mock_logger_error:
            parsed_data = self.scraper.parse_csv('nonexistent_path.csv')

        self.assertEqual(len(parsed_data), 0)
        mock_file_open.assert_called_once_with('nonexistent_path.csv', mode='r', encoding='utf-8-sig')
        mock_logger_error.assert_called()
        self.assertIn("Error parsing CSV file", mock_logger_error.call_args[0][0])


# --- Tests for update_database will go below --- #

class ScraperUpdateDatabaseTests(TestCase):
    """Tests the update_database method of the DecwareOrderScraper."""

    def setUp(self):
        """Set up a scraper instance for database tests."""
        with patch('orders.scraper.DecwareOrderScraper._init_driver', return_value=None):
            self.scraper = DecwareOrderScraper()
        self.scraper.cleanup = lambda: None

    def test_update_db_create_new_orders(self):
        """Test creating new orders in the database."""
        parsed_orders = [
            {'customer_name': 'New Cust 1', 'origin': 'Web', 'quantity': 1, 'model': 'M_NEW1', 'base': 'B1', 'volts': 'V1', 'options': 'O1', 'status': 'NEW', 'order_date': timezone.make_aware(datetime.datetime(2023, 1, 1))},
            {'customer_name': 'New Cust 2', 'origin': 'Mail','quantity': 2, 'model': 'M_NEW2', 'base': 'B2', 'volts': 'V2', 'options': 'O2', 'status': 'PARTS_PULLED', 'order_date': timezone.make_aware(datetime.datetime(2023, 1, 2))}
        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 2)
        self.assertEqual(OrderRecord.objects.count(), 2)
        self.assertEqual(StatusHistory.objects.count(), 2)

        # Check Order 1 details
        order1 = OrderRecord.objects.get(customer_name='New Cust 1')
        self.assertEqual(order1.status, 'NEW')
        self.assertEqual(order1.quantity, 1)
        history1 = StatusHistory.objects.get(order=order1)
        self.assertIsNone(history1.previous_status)
        self.assertEqual(history1.new_status, 'NEW')

        # Check Order 2 details
        order2 = OrderRecord.objects.get(customer_name='New Cust 2')
        self.assertEqual(order2.status, 'PARTS_PULLED')
        self.assertEqual(order2.quantity, 2)
        history2 = StatusHistory.objects.get(order=order2)
        self.assertIsNone(history2.previous_status)
        self.assertEqual(history2.new_status, 'PARTS_PULLED')

    def test_update_db_update_existing_orders_no_status_change(self):
        """Test updating existing orders without status change (no history created)."""
        # Create initial order
        order = OrderRecord.objects.create(
            customer_name='Existing Cust', origin='Web', quantity=1, model='M_EXIST',
            base='Wood', volts='120V', options='Old', status='ON_BENCH',
            order_date=timezone.make_aware(datetime.datetime(2023, 12, 1))
        )
        parsed_orders = [
            { # Match the existing order
                'customer_name': 'Existing Cust', 'origin': 'Web', 'model': 'M_EXIST',
                'base': 'Wood', 'volts': '120V', # Composite key match
                'quantity': 3, 'options': 'Updated', 'status': 'ON_BENCH',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 15))
            }
        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 1)
        self.assertEqual(OrderRecord.objects.count(), 1)
        # Status history should NOT increase
        self.assertEqual(StatusHistory.objects.count(), 0)

        updated_order = OrderRecord.objects.get(pk=order.pk)
        self.assertEqual(updated_order.quantity, 3)
        self.assertEqual(updated_order.options, 'Updated')
        self.assertEqual(updated_order.order_date, timezone.make_aware(datetime.datetime(2023, 12, 15)))
        self.assertEqual(updated_order.status, 'ON_BENCH')

    def test_update_db_update_existing_orders_with_status_change(self):
        """Test updating existing orders WITH a status change (history created)."""
        # Create an initial order
        initial_status = 'ON_BENCH'
        order = OrderRecord.objects.create(
            customer_name='Existing Cust', origin='Web', quantity=1, model='M_EXIST',
            base='Wood', volts='120V', options='Old', status=initial_status,
            order_date=timezone.make_aware(datetime.datetime(2023, 12, 1))
        )
        parsed_orders = [
            { # Match the existing order
                'customer_name': 'Existing Cust', 'origin': 'Web', 'model': 'M_EXIST',
                'base': 'Wood', 'volts': '120V',
                # Update status
                'quantity': 1, 'options': 'Old', 'status': 'TESTING',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 1))
            }
        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 1)
        self.assertEqual(OrderRecord.objects.count(), 1)
        # Status history SHOULD increase
        self.assertEqual(StatusHistory.objects.count(), 1)

        updated_order = OrderRecord.objects.get(pk=order.pk)
        self.assertEqual(updated_order.status, 'TESTING')

        # Check the new history entry
        latest_history = StatusHistory.objects.filter(order=updated_order).latest('timestamp')
        self.assertEqual(latest_history.previous_status, 'ON_BENCH')
        self.assertEqual(latest_history.new_status, 'TESTING')

    def test_update_db_mixed_create_and_update(self):
        """Test a batch containing both new orders and updates."""
        # Existing order
        existing_order = OrderRecord.objects.create(
            customer_name='Existing Cust', origin='Web', quantity=1, model='M_EXIST',
            base='Wood', volts='120V', options='Old', status='NEW',
            order_date=timezone.make_aware(datetime.datetime(2023, 12, 1))
        )
        parsed_orders = [
            # Update existing order (change status)
            {
                'customer_name': 'Existing Cust', 'origin': 'Web', 'model': 'M_EXIST',
                'base': 'Wood', 'volts': '120V', # Composite key match
                'quantity': 2, 'options': 'Updated', 'status': 'PARTS_PULLED',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 1))
            },
            # Create new order
            {
                'customer_name': 'New Cust', 'origin': 'Mail', 'quantity': 1, 'model': 'M_NEW',
                'base': 'Plastic', 'volts': '240V', 'options': 'None', 'status': 'NEW',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 15))
            },

        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 2)
        self.assertEqual(OrderRecord.objects.count(), 2)
        # 1 initial + 1 status change + 1 new order = 2 history entries
        self.assertEqual(StatusHistory.objects.count(), 2)

        updated_mixed = OrderRecord.objects.get(pk=existing_order.pk)
        self.assertEqual(updated_mixed.status, 'PARTS_PULLED')
        self.assertEqual(updated_mixed.quantity, 2)
        self.assertEqual(updated_mixed.options, 'Updated')

        new_other = OrderRecord.objects.get(customer_name='New Cust')
        self.assertEqual(new_other.status, 'NEW')

        # Check history counts per order
        self.assertEqual(StatusHistory.objects.filter(order=updated_mixed).count(), 1)
        self.assertEqual(StatusHistory.objects.filter(order=new_other).count(), 1)

    @patch('orders.scraper.logger.error')
    def test_update_db_handles_exception(self, mock_logger_error):
        """Test that processing continues after an error on one order."""
        parsed_orders = [
            # Valid new order
            {
                'customer_name': 'Good Cust', 'origin': 'Web', 'quantity': 1, 'model': 'M_GOOD',
                'base': 'Good', 'volts': '120V', 'options': 'Opt', 'status': 'NEW',
                'order_date': timezone.make_aware(datetime.datetime(2023, 1, 1))
            },
            # Order that will cause an error (e.g., mock update_or_create failure)
            {
                'customer_name': 'Bad Cust', 'origin': 'Web', 'quantity': 1, 'model': 'M_BAD',
                'base': 'Bad', 'volts': '120V', 'options': 'Opt', 'status': 'NEW',
                'order_date': timezone.make_aware(datetime.datetime(2023, 1, 1))
            },
            # Another valid new order
            {
                'customer_name': 'Good Cust 2', 'origin': 'Phone', 'quantity': 1, 'model': 'M_GOOD2',
                'base': 'Good2', 'volts': '240V', 'options': 'Opt2', 'status': 'NEW',
                'order_date': timezone.make_aware(datetime.datetime(2023, 1, 2))
            },
        ]

        # Mock update_or_create to fail for the 'Bad Cust'
        original_update_or_create = OrderRecord.objects.update_or_create
        def side_effect(*args, **kwargs):
            if kwargs.get('customer_name') == 'Bad Cust':
                raise ValueError("Simulated database error")
            # Call the original function for other cases
            # Need to handle both positional and keyword args depending on how it's called
            if args:
                 return original_update_or_create(*args, **kwargs)
            else:
                 return original_update_or_create(**kwargs)


        with patch.object(OrderRecord.objects, 'update_or_create', side_effect=side_effect):
            orders_processed = self.scraper.update_database(parsed_orders)

        # Should process 2 out of 3 (the good ones)
        self.assertEqual(orders_processed, 2)
        # Database should contain only the 2 good orders
        self.assertEqual(OrderRecord.objects.count(), 2)
        self.assertTrue(OrderRecord.objects.filter(customer_name='Good Cust').exists())
        self.assertTrue(OrderRecord.objects.filter(customer_name='Good Cust 2').exists())
        self.assertFalse(OrderRecord.objects.filter(customer_name='Bad Cust').exists())
        # History should exist only for the 2 good orders
        self.assertEqual(StatusHistory.objects.count(), 2)

        # Check that the error was logged
        mock_logger_error.assert_called()
        self.assertIn("Error processing order", mock_logger_error.call_args[0][0])
        self.assertIn("'customer_name': 'Bad Cust'", str(mock_logger_error.call_args[0][0]))

# ==================================
# Integration Tests (Mocking Download)
# ==================================

class ScraperDownloadIntegrationTests(TestCase):
    """Tests the integration between download_csv and parse_csv, mocking web interactions."""

    def setUp(self):
        """Set up a temporary directory and dummy CSV file for each test."""
        self.temp_download_dir = tempfile.mkdtemp()
        self.dummy_csv_path = os.path.join(self.temp_download_dir, 'decware_orders_integration_test.csv')
        self.csv_content = (
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\r\n' # Note: \r\n line endings
            '"Integration User","Web","1","INT-MOD-A","Base-A","120V","Opt-A","New","2024-07-31 10:00:00"\r\n'
            '"Another User","Mail","2","INT-MOD-B","Base-B","240V","Opt-B","Parts Pulled","2024-07-31 11:30:00"\r\n'
        )
        # Write with utf-8-sig encoding to mimic potential real download
        with open(self.dummy_csv_path, 'w', encoding='utf-8-sig') as f:
            f.write(self.csv_content)

        # Instantiate scraper
        self.scraper = DecwareOrderScraper()
        # Override the download directory to our temp one BEFORE calling download
        self.scraper.download_dir = self.temp_download_dir
        # Prevent actual file cleanup by the scraper
        self.scraper.cleanup = lambda: None

    def tearDown(self):
        """Clean up the temporary download directory."""
        shutil.rmtree(self.temp_download_dir)

    @patch('orders.scraper.webdriver.Chrome') # Mock the browser object creation
    @patch('orders.scraper.os.path.getctime') # Mock file timestamp check
    @patch('orders.scraper.os.listdir')      # Mock directory listing
    @patch('orders.scraper.WebDriverWait')    # Mock the explicit wait
    def test_download_and_parse_integration(self, mock_wait, mock_listdir, mock_getctime, MockWebDriver):
        """
        Test the integration of downloading (mocked) and parsing a CSV file.
        Mocks the actual browser interaction but tests file handling and parsing coordination.
        """
        # --- Arrange Mocks --- 
        # Mock the driver instance returned by Chrome()
        mock_driver = MockWebDriver.return_value
        self.scraper.driver = mock_driver # Ensure scraper uses the mock driver

        # --- Setup Mock Behavior --- 
        # Mock the WebDriverWait().until() call to return a mock button immediately
        mock_button = MagicMock()
        mock_wait_instance = mock_wait.return_value
        mock_wait_instance.until.return_value = mock_button

        # Mock os functions to simulate immediate file discovery in download_csv loop
        dummy_filename = os.path.basename(self.dummy_csv_path)
        mock_listdir.return_value = [dummy_filename]
        mock_getctime.return_value = time.time() # Just need a consistent value
        
        # --- Act --- 
        # Call download_csv. It should use mocked browser and mocked os functions.
        returned_path = self.scraper.download_csv()

        # Verify that the download process returned the expected path
        self.assertEqual(returned_path, self.dummy_csv_path)

        # Now, use the returned path to parse the CSV
        parsed_data = self.scraper.parse_csv(returned_path)

        # --- Assert --- 
        # Check if the parsed data matches the contents of our dummy CSV
        self.assertEqual(len(parsed_data), 2)

        # Check Order 1
        order1 = parsed_data[0]
        self.assertEqual(order1['customer_name'], 'Integration User')
        self.assertEqual(order1['origin'], 'Web')
        self.assertEqual(order1['quantity'], 1)
        self.assertEqual(order1['model'], 'INT-MOD-A')
        self.assertEqual(order1['status'], 'NEW')
        expected_dt1 = timezone.make_aware(datetime.datetime(2024, 7, 31, 10, 0, 0))
        self.assertEqual(order1['order_date'], expected_dt1)

        # Check Order 2
        order2 = parsed_data[1]
        self.assertEqual(order2['customer_name'], 'Another User')
        self.assertEqual(order2['quantity'], 2)
        self.assertEqual(order2['model'], 'INT-MOD-B')
        self.assertEqual(order2['status'], 'PARTS_PULLED')
        expected_dt2 = timezone.make_aware(datetime.datetime(2024, 7, 31, 11, 30, 0))
        self.assertEqual(order2['order_date'], expected_dt2)

        # --- Verify Mocks --- 
        # Check that the mocked methods were called as expected
        mock_driver.get.assert_called_once_with(self.scraper.PAGE_URL) # Check if URL was loaded
        # WebDriverWait().until is mocked, so find_element is not directly called by test code
        # Verify the wait was instantiated and until was called
        mock_wait.assert_called_once_with(mock_driver, self.scraper.TIMEOUT)
        mock_wait_instance.until.assert_called_once()
        # Check that the button mock was clicked
        mock_button.click.assert_called_once()
        # Verify os mocks were called by the download_csv loop
        mock_listdir.assert_called_once_with(self.scraper.download_dir)
        mock_getctime.assert_called_once_with(self.dummy_csv_path)

# ==================================
# Database Update Tests
# ==================================
