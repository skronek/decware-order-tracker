"""
Django management command to update order data from orders.decware.com.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.scraper import DecwareOrderScraper


class Command(BaseCommand):
    help = 'Downloads and processes order data from orders.decware.com'

    def handle(self, *args, **options):
        scraper = DecwareOrderScraper()
        
        self.stdout.write(
            self.style.HTTP_INFO(f"Starting order update at {timezone.now()}")
        )
        
        success = scraper.run()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("Successfully updated order data")
            )
        else:
            self.stdout.write(
                self.style.ERROR("Failed to update order data")
            )
