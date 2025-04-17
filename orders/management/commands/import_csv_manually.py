import os
import logging
from django.core.management.base import BaseCommand
from orders.scraper import DecwareOrderScraper

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import orders from a manually downloaded CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to the CSV file')
        parser.add_argument('--dry-run', action='store_true', help='Run without making changes to the database')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        dry_run = options['dry_run']
        
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
            return
        
        self.stdout.write(f"Importing orders from {csv_path}")
        
        # Create scraper instance
        scraper = DecwareOrderScraper()
        
        # Parse CSV and update orders
        try:
            # Parse the CSV file
            orders = scraper.parse_csv(csv_path)
            
            if not orders:
                self.stderr.write(self.style.ERROR("No orders could be parsed from the CSV."))
                return
                
            self.stdout.write(f"Found {len(orders)} orders in CSV")
            
            # Update the database with the parsed orders
            if not dry_run:
                updated, created = scraper.update_orders(orders)
                self.stdout.write(self.style.SUCCESS(f"Updated {updated} orders, created {created} new orders"))
            else:
                self.stdout.write(self.style.WARNING("DRY RUN - No changes made to database"))
                for i, order in enumerate(orders[:5]):  # Show first 5 orders as preview
                    self.stdout.write(f"Order {i+1}: {order.get('customer_name', 'Unknown')} - {order.get('model', 'Unknown')} - {order.get('order_date', 'Unknown')}")
                if len(orders) > 5:
                    self.stdout.write(f"... and {len(orders) - 5} more orders")
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during import: {str(e)}"))
