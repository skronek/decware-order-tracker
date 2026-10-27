from django.contrib import admin
from .models import OrderEstimate, OrderRecord, StatusHistory, StatusMetrics


# Register your models here.

@admin.register(OrderRecord)
class OrderRecordAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'model', 'status', 'time_created', 'time_updated', 'removed_at')
    list_filter = ('status', 'model')
    search_fields = ('customer_name', 'model')
    ordering = ('-time_updated',)


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('previous_status', 'new_status')
    search_fields = ('order__customer_name',)
    ordering = ('-timestamp',)


@admin.register(StatusMetrics)
class StatusMetricsAdmin(admin.ModelAdmin):
    list_display = ('status', 'average_time_days', 'sample_size', 'confidence_level', 'last_updated')
    list_filter = ('confidence_level',)
    ordering = ('status',)


@admin.register(OrderEstimate)
class OrderEstimateAdmin(admin.ModelAdmin):
    list_display = ('order', 'queue_position', 'estimated_date', 'range_end_date', 'confidence_level', 'computed_at')
    list_filter = ('confidence_level',)
    search_fields = ('order__customer_name',)
    ordering = ('estimated_date',)
