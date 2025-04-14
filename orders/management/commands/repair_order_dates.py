"""
Django management command to repair null order dates.
"""
import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from orders.models import OrderRecord
from orders.scraper import DecwareOrderScraper

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Identifies and repairs orders with null date values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no changes will be made)',
        )
        parser.add_argument(
            '--repair-method',
            choices=['status_history', 'creation_time', 'default_date'],
            default='status_history',
            help='Method to use for repairing null dates',
        )
        parser.add_argument(
            '--default-date',
            help='Default date to use if repair-method is default_date (format: YYYY-MM-DD)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        repair_method = options['repair_method']
        default_date_str = options.get('default_date')
        
        # Initialize the date cleaner
        scraper = DecwareOrderScraper()
        
        # Find orders with null dates
        null_date_orders = OrderRecord.objects.filter(order_date__isnull=True)
        count = null_date_orders.count()
        
        self.stdout.write(f"Found {count} orders with null dates")
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No orders with null dates found. Database is clean!"))
            return
        
        # Process each order
        repaired_count = 0
        failed_count = 0
        
        for order in null_date_orders:
            try:
                # Try to repair the date
                if repair_method == 'status_history':
                    # Use the earliest status history timestamp
                    if order.status_history.exists():
                        earliest_status = order.status_history.order_by('timestamp').first()
                        new_date = earliest_status.timestamp
                        self.stdout.write(f"Order {order.id}: Using earliest status history timestamp: {new_date}")
                    else:
                        # Fall back to creation time if no status history
                        new_date = order.time_created
                        self.stdout.write(f"Order {order.id}: No status history, using creation time: {new_date}")
                
                elif repair_method == 'creation_time':
                    # Use the order creation timestamp
                    new_date = order.time_created
                    self.stdout.write(f"Order {order.id}: Using creation time: {new_date}")
                
                elif repair_method == 'default_date':
                    # Use the provided default date
                    if not default_date_str:
                        self.stdout.write(self.style.ERROR(
                            f"Order {order.id}: No default date provided for default_date method"
                        ))
                        failed_count += 1
                        continue
                    
                    try:
                        default_date = datetime.datetime.strptime(default_date_str, '%Y-%m-%d')
                        new_date = timezone.make_aware(default_date)
                        self.stdout.write(f"Order {order.id}: Using default date: {new_date}")
                    except ValueError:
                        self.stdout.write(self.style.ERROR(
                            f"Order {order.id}: Invalid default date format: {default_date_str}"
                        ))
                        failed_count += 1
                        continue
                
                # Apply the repair if not in dry-run mode
                if not dry_run:
                    order.order_date = new_date
                    order.save(update_fields=['order_date'])
                    self.stdout.write(self.style.SUCCESS(
                        f"Order {order.id}: Repaired date to {new_date}"
                    ))
                else:
                    self.stdout.write(
                        f"Order {order.id}: Would repair date to {new_date} (dry run)"
                    )
                
                repaired_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Order {order.id}: Failed to repair date: {str(e)}"
                ))
                failed_count += 1
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"Dry run completed. Would repair {repaired_count} orders. {failed_count} orders would fail."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Repair completed. Repaired {repaired_count} orders. {failed_count} orders failed."
            ))
