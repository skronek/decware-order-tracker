from django.db import models
from django.utils import timezone


class OrderRecord(models.Model):
    # Status choices based on PRD requirements
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('PARTS_PULLED', 'Parts Pulled'),
        ('ON_BENCH', 'On Bench'),
        ('TESTING', 'Testing'),
        ('QUALITY_CONTROL', 'Quality Control'),
        ('PASSED_QC', 'Passed Quality Control'),
        ('PASSED_QC_AWAITING_PAYMENT', 'Passed Quality Control - Awaiting Payment'),
        ('COMPLETED_WAITING_BASE', 'Completed waiting for wood base'),
    ]

    # Customer information
    customer_name = models.CharField(max_length=255, db_index=True)
    origin = models.CharField(max_length=255)

    # Product information
    model = models.CharField(max_length=100, db_index=True)
    base = models.CharField(max_length=100, blank=True, default='')
    volts = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    options = models.TextField(blank=True)

    # Status and timestamps
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, db_index=True, null=False, default='NEW')
    order_date = models.DateTimeField(default=timezone.now) # Date the order was placed (from CSV)
    time_created = models.DateTimeField(default=timezone.now)
    time_updated = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)  # Last scraper run that found this order in the CSV
    removed_at = models.DateTimeField(null=True, blank=True)  # First scraper run that no longer found it (order finished)

    class Meta:
        indexes = [
            models.Index(fields=['customer_name', 'model']),  # Optimize search by name and model
            models.Index(fields=['status', 'time_updated']),  # Optimize status-based queries
        ]
        ordering = ['-time_updated']  # Most recently updated first

    def __str__(self):
        return f"{self.customer_name} - {self.model} ({self.status})"


class StatusHistory(models.Model):
    order = models.ForeignKey(OrderRecord, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=50, choices=OrderRecord.STATUS_CHOICES, null=True, blank=True) # Allow null for initial status
    new_status = models.CharField(max_length=50, choices=OrderRecord.STATUS_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    # False when the timestamp isn't when the change really happened: the first row for
    # an order (it may have been in that status for a while), or a change spotted after
    # the scraper missed days of runs.
    is_observed = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['order', '-timestamp']),  # Optimize status history retrieval
        ]
        ordering = ['-timestamp']  # Most recent status changes first

    def __str__(self):
        return f"{self.order.customer_name} - {self.previous_status} → {self.new_status}"


class OrderEstimate(models.Model):
    """Estimated Passed QC date for an active order, recomputed after each scraper run."""
    order = models.OneToOneField(OrderRecord, on_delete=models.CASCADE, related_name='estimate')
    estimated_date = models.DateField(help_text="Most likely date the order passes QC (the best guess)")
    range_start_date = models.DateField(help_text="Earlier end of the likely range")
    range_end_date = models.DateField(help_text="Later end of the likely range")
    queue_position = models.PositiveIntegerField(null=True, blank=True, help_text="Orders ahead of this one waiting to start")
    confidence_level = models.CharField(
        max_length=10,
        choices=[('HIGH', 'High'), ('MEDIUM', 'Medium'), ('LOW', 'Low')],
    )
    explanation = models.TextField(blank=True, default='', help_text="Customer-facing sentence explaining the estimate")
    computed_at = models.DateTimeField()

    def __str__(self):
        return f"{self.order} - {self.estimated_date} ({self.range_start_date} to {self.range_end_date}, {self.confidence_level})"
