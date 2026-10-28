"""
Tests for date parsing functionality in the scraper module.
"""
import datetime
from django.test import TestCase
from django.utils import timezone

from .scraper import DecwareOrderScraper

class DateParsingTests(TestCase):
    """Test cases for date parsing functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.scraper = DecwareOrderScraper()
    
    def test_clean_date_string(self):
        """Test cleaning date strings with invisible characters."""
        # Test with zero-width space
        date_with_zwsp = "2023-04-15 14:30:00\u200b"
        cleaned = self.scraper._clean_date_string(date_with_zwsp)
        self.assertEqual(cleaned, "2023-04-15 14:30:00")
        
        # Test with non-breaking space
        date_with_nbsp = "2023-04-15\xa014:30:00"
        cleaned = self.scraper._clean_date_string(date_with_nbsp)
        self.assertEqual(cleaned, "2023-04-15 14:30:00")
        
        # Test with multiple spaces
        date_with_spaces = "2023-04-15  14:30:00"
        cleaned = self.scraper._clean_date_string(date_with_spaces)
        self.assertEqual(cleaned, "2023-04-15 14:30:00")
        
        # Test with leading/trailing spaces
        date_with_spaces = " 2023-04-15 14:30:00 "
        cleaned = self.scraper._clean_date_string(date_with_spaces)
        self.assertEqual(cleaned, "2023-04-15 14:30:00")
        
        # Test with multiple invisible characters
        date_with_multiple = "2023-04-15\u200b\xa014:30:00\u200b"
        cleaned = self.scraper._clean_date_string(date_with_multiple)
        self.assertEqual(cleaned, "2023-04-15 14:30:00")
    
    def test_parse_csv_with_problematic_dates(self):
        """Test parsing CSV with problematic date formats."""
        # This is a more complex test that would require creating a temporary CSV file
        # with problematic dates. For simplicity, we'll just test the core functionality.
        import tempfile
        import csv
        import os
        
        # Create a temporary CSV file with problematic dates
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            fieldnames = ['For', 'From', 'MODEL', 'Base', 'VOLTS', 'Options', 'Status', 'Date-Time']
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            
            # Row with normal date
            writer.writerow({
                'For': 'Test Customer 1',
                'From': 'Test Origin 1',
                'MODEL': 'Test Model 1',
                'Base': 'Test Base 1',
                'VOLTS': '110V',
                'Options': 'None',
                'Status': 'NEW',
                'Date-Time': '2023-04-15 14:30:00'
            })
            
            # Row with zero-width space in date
            writer.writerow({
                'For': 'Test Customer 2',
                'From': 'Test Origin 2',
                'MODEL': 'Test Model 2',
                'Base': 'Test Base 2',
                'VOLTS': '220V',
                'Options': 'None',
                'Status': 'NEW',
                'Date-Time': '2023-04-15 14:30:00\u200b'
            })
            
            # Row with non-breaking space in date
            writer.writerow({
                'For': 'Test Customer 3',
                'From': 'Test Origin 3',
                'MODEL': 'Test Model 3',
                'Base': 'Test Base 3',
                'VOLTS': '110V',
                'Options': 'None',
                'Status': 'NEW',
                'Date-Time': '2023-04-15\xa014:30:00'
            })
            
            temp_file_path = temp_file.name
        
        try:
            # Parse the CSV file
            orders = self.scraper.parse_csv(temp_file_path)
            
            # Check that we got 3 orders
            self.assertEqual(len(orders), 3)
            
            # Check that all orders have a valid order_date
            for order in orders:
                self.assertIn('order_date', order)
                self.assertIsNotNone(order['order_date'])
                
                # Check that the order_date is a timezone-aware datetime
                self.assertTrue(timezone.is_aware(order['order_date']))
                
                # Check that the date part is correct (all should be 2023-04-15)
                self.assertEqual(order['order_date'].date(), datetime.date(2023, 4, 15))
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
