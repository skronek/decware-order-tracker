"""
Django management command to load sample order data.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from orders.scraper import DecwareOrderScraper


class Command(BaseCommand):
    help = 'Loads sample order data from the sample_data directory'

    def handle(self, *args, **options):
        sample_csv = os.path.join(settings.BASE_DIR, 'sample_data', 'orders.csv')
        if not os.path.exists(sample_csv):
            self.stdout.write(
                self.style.ERROR(f"Sample data file not found: {sample_csv}")
            )
            return

        scraper = DecwareOrderScraper()
        orders = scraper.parse_csv(sample_csv)
        
        if not orders:
            self.stdout.write(
                self.style.ERROR("No orders found in sample data")
            )
            return
            
        orders_processed = scraper.update_database(orders)
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully loaded {orders_processed} sample orders")
        )
