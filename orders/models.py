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

    class Meta:
        indexes = [
            models.Index(fields=['order', '-timestamp']),  # Optimize status history retrieval
        ]
        ordering = ['-timestamp']  # Most recent status changes first

    def __str__(self):
        return f"{self.order.customer_name} - {self.previous_status} → {self.new_status}"


class StatusMetrics(models.Model):
    status = models.CharField(max_length=50, choices=OrderRecord.STATUS_CHOICES, unique=True)
    average_time_days = models.FloatField(help_text="Average time spent in this status in days")
    sample_size = models.PositiveIntegerField(help_text="Number of orders used to calculate the average")
    last_updated = models.DateTimeField(auto_now=True)
    confidence_level = models.CharField(
        max_length=10,
        choices=[('HIGH', 'High'), ('LOW', 'Low')],
        help_text="Confidence level in the average time calculation"
    )

    class Meta:
        verbose_name_plural = "Status metrics"

    def __str__(self):
        return f"{self.status} - {self.average_time_days:.1f} days (Confidence: {self.confidence_level})"
