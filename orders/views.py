from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import OrderRecord, StatusHistory
from .serializers import OrderRecordSerializer, StatusHistorySerializer
from .filters import OrderRecordFilterSet


class OrderRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing order records.
    Supports exact lookup via customer_name, origin, model, base, and volts parameters.
    """
    queryset = OrderRecord.objects.all().select_related('estimate').prefetch_related('status_history')
    serializer_class = OrderRecordSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = OrderRecordFilterSet
    ordering_fields = ['time_created', 'time_updated', 'status']
    ordering = ['-time_updated']


class StatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StatusHistorySerializer
    queryset = StatusHistory.objects.all()
