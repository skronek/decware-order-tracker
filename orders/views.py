from django.shortcuts import render
from django.db.models import Q
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import OrderRecord, StatusMetrics, StatusHistory
from .serializers import OrderRecordSerializer, StatusMetricsSerializer, StatusHistorySerializer
from .filters import OrderRecordFilterSet


# Create your views here.

class OrderRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing order records.
    Supports exact lookup via customer_name, origin, model, base, and volts parameters.
    """
    serializer_class = OrderRecordSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]  # Re-enable ordering
    filterset_class = OrderRecordFilterSet
    # Temporarily remove 'status' to check for conflicts
    ordering_fields = ['time_created', 'time_updated', 'status']
    ordering = ['-time_updated']  # Default ordering
    
    def get_queryset(self):
        """
        Get the list of orders for this view.
        Filters based on provided query parameters:
        customer_name, origin, model, base, volts, status.
        """
        # Base queryset, filtering is handled by DjangoFilterBackend
        queryset = OrderRecord.objects.all().select_related('estimate').prefetch_related('status_history')
        return queryset

class StatusMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing status metrics.
    Provides average time spent in each status.
    """
    queryset = StatusMetrics.objects.all().order_by('status')
    serializer_class = StatusMetricsSerializer
    lookup_field = 'status'  # Use the unique 'status' field for detail view lookups

class StatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StatusHistorySerializer
    queryset = StatusHistory.objects.all() # Define the base queryset
