from datetime import timedelta

from django.db.models import Max
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
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


# The scraper runs daily; allow a missed hour or two before calling it stale.
MAX_SCRAPE_AGE = timedelta(hours=36)


@api_view(['GET'])
def health(request):
    """
    Uptime-monitor endpoint: 200 if the scraper ran recently, 503 if not.
    The newest last_seen_at is the time of the last successful scrape.
    """
    last_scrape = OrderRecord.objects.aggregate(Max('last_seen_at'))['last_seen_at__max']
    healthy = last_scrape is not None and timezone.now() - last_scrape <= MAX_SCRAPE_AGE
    return Response(
        {'status': 'ok' if healthy else 'stale', 'last_scrape': last_scrape},
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
