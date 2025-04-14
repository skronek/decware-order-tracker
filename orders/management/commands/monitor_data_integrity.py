"""
Django management command to monitor data integrity.
This command checks for various data integrity issues and reports them.
"""
import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings

from orders.models import OrderRecord, StatusHistory

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Monitors data integrity and reports issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            help='Email address to send the report to',
        )
        parser.add_argument(
            '--no-output',
            action='store_true',
            help='Suppress console output',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        no_output = options.get('no_output', False)
        
        # Initialize the report
        report_lines = []
        issues_found = False
        
        # Check for null dates
        null_date_count = OrderRecord.objects.filter(order_date__isnull=True).count()
        if null_date_count > 0:
            issues_found = True
            message = f"ISSUE: Found {null_date_count} orders with null dates"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.ERROR(message))
        else:
            message = "OK: No orders with null dates found"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.SUCCESS(message))
        
        # Check for future dates (potential errors)
        future_date_count = OrderRecord.objects.filter(order_date__gt=timezone.now()).count()
        if future_date_count > 0:
            issues_found = True
            message = f"ISSUE: Found {future_date_count} orders with future dates"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.ERROR(message))
        else:
            message = "OK: No orders with future dates found"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.SUCCESS(message))
        
        # Check for orders without status history
        no_history_count = OrderRecord.objects.annotate(
            history_count=Count('status_history')
        ).filter(history_count=0).count()
        
        if no_history_count > 0:
            issues_found = True
            message = f"ISSUE: Found {no_history_count} orders without status history"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.ERROR(message))
        else:
            message = "OK: All orders have status history"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.SUCCESS(message))
        
        # Check for inconsistent status between OrderRecord and StatusHistory
        inconsistent_status_count = 0
        for order in OrderRecord.objects.all():
            latest_status_history = order.status_history.order_by('-timestamp').first()
            if latest_status_history and latest_status_history.new_status != order.status:
                inconsistent_status_count += 1
        
        if inconsistent_status_count > 0:
            issues_found = True
            message = f"ISSUE: Found {inconsistent_status_count} orders with inconsistent status"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.ERROR(message))
        else:
            message = "OK: All orders have consistent status"
            report_lines.append(message)
            if not no_output:
                self.stdout.write(self.style.SUCCESS(message))
        
        # Send email report if requested and issues were found
        if email and issues_found:
            report_text = "\n".join(report_lines)
            subject = f"Decware Order Tracker - Data Integrity Report - {timezone.now().strftime('%Y-%m-%d')}"
            
            try:
                send_mail(
                    subject=subject,
                    message=report_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                if not no_output:
                    self.stdout.write(self.style.SUCCESS(f"Sent report to {email}"))
            except Exception as e:
                if not no_output:
                    self.stdout.write(self.style.ERROR(f"Failed to send email: {str(e)}"))
        
        # Final summary
        if issues_found:
            if not no_output:
                self.stdout.write(self.style.ERROR("Data integrity check completed with issues"))
            return 1  # Return non-zero exit code to indicate issues
        else:
            if not no_output:
                self.stdout.write(self.style.SUCCESS("Data integrity check completed successfully"))
            return 0  # Return zero exit code to indicate success
