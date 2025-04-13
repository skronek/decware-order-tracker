from rest_framework import serializers
from django.db import models, connection
from django.utils import timezone
from datetime import timedelta
from .models import OrderRecord, StatusHistory, StatusMetrics


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
            'status_history', 'estimated_completion', 'order_date'
        ]
    
    def get_estimated_completion(self, obj):
        """
        Calculate estimated completion date based on the average time it takes for orders 
        to reach the 'PASSED_QC_AWAITING_PAYMENT' status.
        
        Uses the formula: order_date + avg(now - order_date) for orders with status='PASSED_QC_AWAITING_PAYMENT'
        """
        try:
            # If the order is already completed or awaiting payment, return None
            if obj.status in ['PASSED_QC_AWAITING_PAYMENT', 'COMPLETED_WAITING_BASE']:
                return None
            
            # Use raw SQL to get the average time to completion
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT ROUND(AVG((NOW()::date - order_date::date)), 0)::int
                FROM orders_orderrecord
                WHERE status = 'PASSED_QC_AWAITING_PAYMENT'
                GROUP BY status
                """)
                row = cursor.fetchone()
                
                if not row or row[0] is None:
                    return None
                
                avg_days_to_completion = row[0]
                
                # Calculate estimated completion date
                if obj.order_date:
                    completion_date = obj.order_date.date() + timedelta(days=avg_days_to_completion)
                    days_remaining = (completion_date - timezone.now().date()).days
                    
                    return {
                        'days_remaining': days_remaining,
                        'estimated_date': completion_date.isoformat(),
                        'confidence_level': 0.7  # Default confidence level
                    }
                
            return {
                'days_remaining': None,
                'estimated_date': None,
                'confidence_level': None
            }
        except Exception as e:
            print(f"Error calculating estimated completion: {e}")
            return None
    
    def _get_remaining_statuses(self, current_status):
        """Get list of statuses that come after the current status."""
        status_order = [
            'NEW',
            'PARTS_PULLED',
            'ON_BENCH',
            'TESTING',
            'QUALITY_CONTROL',
            'PASSED_QC',
            'PASSED_QC_AWAITING_PAYMENT',
            'COMPLETED_WAITING_BASE'
        ]
        try:
            current_index = status_order.index(current_status)
            return status_order[current_index + 1:]
        except (ValueError, IndexError):
            return []


class StatusMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusMetrics
        fields = ['status', 'average_time_days', 'sample_size', 'confidence_level', 'last_updated']
