from rest_framework import serializers
from django.utils import timezone
from .models import OrderRecord, OrderEstimate, StatusHistory, StatusMetrics


class StatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusHistory
        fields = ['id', 'order', 'previous_status', 'new_status', 'timestamp']


class OrderRecordSerializer(serializers.ModelSerializer):
    status_history = StatusHistorySerializer(many=True, read_only=True)
    estimated_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderRecord
        fields = [
            'id', 'customer_name', 'origin', 'model', 'base', 'volts',
            'quantity', 'options', 'status', 'time_created', 'time_updated',
            'status_history', 'estimated_completion', 'order_date',
            'last_seen_at', 'removed_at'
        ]
    
    def get_estimated_completion(self, obj):
        """
        The stored estimate of when the order passes QC (see orders/estimation.py),
        or None for orders that are finished or not yet estimated.
        """
        try:
            estimate = obj.estimate
        except OrderEstimate.DoesNotExist:
            return None
        return {
            'estimated_date': estimate.estimated_date.isoformat(),
            'range_end_date': estimate.range_end_date.isoformat(),
            'days_remaining': max(0, (estimate.estimated_date - timezone.localdate()).days),
            'queue_position': estimate.queue_position,
            'confidence_level': estimate.confidence_level,
        }


class StatusMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusMetrics
        fields = ['status', 'average_time_days', 'sample_size', 'confidence_level', 'last_updated']
