import django_filters
from .models import OrderRecord

class OrderRecordFilterSet(django_filters.FilterSet):
    # Define filters for OrderRecord fields
    # Default lookup_expr is 'exact'
    customer_name = django_filters.CharFilter(lookup_expr='iexact')  # Case-insensitive
    origin = django_filters.CharFilter(lookup_expr='iexact')  # Case-insensitive
    model = django_filters.CharFilter(lookup_expr='iexact')  # Case-insensitive
    base = django_filters.CharFilter(lookup_expr='iexact')  # Case-insensitive
    volts = django_filters.CharFilter(lookup_expr='iexact')  # Case-insensitive
    status = django_filters.CharFilter(lookup_expr='iexact') # Case-insensitive for status

    class Meta:
        model = OrderRecord
        fields = ['customer_name', 'origin', 'model', 'base', 'volts', 'status']
