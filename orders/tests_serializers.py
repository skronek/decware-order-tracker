from django.test import TestCase
from django.utils import timezone
from .models import OrderRecord, StatusHistory
from .serializers import StatusHistorySerializer, OrderRecordSerializer, StatusMetricsSerializer
from decimal import Decimal
import datetime

class StatusHistorySerializerTests(TestCase):
    """Tests for the StatusHistorySerializer."""
    @classmethod
    def setUpTestData(cls):
        cls.order = OrderRecord.objects.create(customer_name="Serializer Test", model="TestM", status="INITIAL")
        cls.timestamp = timezone.now()
        cls.history_entry = StatusHistory.objects.create(
            order=cls.order,
            previous_status="INITIAL",
            new_status="PROCESSING",
            timestamp=cls.timestamp
        )

    def test_serialization(self):
        """Test that the serializer outputs the expected fields and values."""
        serializer = StatusHistorySerializer(instance=self.history_entry)
        data = serializer.data

        self.assertEqual(len(data.keys()), 6) # Expecting 6 fields: id, order, previous_status, new_status, timestamp, is_observed
        self.assertEqual(data['previous_status'], "INITIAL")
        self.assertEqual(data['new_status'], "PROCESSING")
        # Compare timestamp after formatting as serializer does
        self.assertEqual(data['timestamp'], self.timestamp.isoformat().replace('+00:00', 'Z'))
        self.assertIs(data['is_observed'], True)

    def test_serializes_unobserved_change(self):
        """Changes whose timestamp isn't when they really happened are flagged."""
        entry = StatusHistory.objects.create(
            order=self.order, previous_status="PROCESSING", new_status="DONE", is_observed=False
        )
        self.assertIs(StatusHistorySerializer(instance=entry).data['is_observed'], False)

class OrderRecordSerializerTests(TestCase):
    """Tests for the OrderRecordSerializer."""
    @classmethod
    def setUpTestData(cls):
        cls.order_date = timezone.make_aware(datetime.datetime(2024, 1, 1, 10, 0, 0))
        cls.order = OrderRecord.objects.create(
            customer_name="Record Test",
            origin="USA",
            model="SE84UFO",
            base="Walnut",
            volts="120",
            quantity=1,
            options="No options",
            status="ON_BENCH",
            order_date=cls.order_date
        )
        # Add history
        cls.hist1_ts = cls.order.time_created + datetime.timedelta(days=1)
        cls.hist2_ts = cls.order.time_created + datetime.timedelta(days=2)
        StatusHistory.objects.create(order=cls.order, previous_status="NEW", new_status="PARTS_PULLED", timestamp=cls.hist1_ts)
        StatusHistory.objects.create(order=cls.order, previous_status="PARTS_PULLED", new_status="ON_BENCH", timestamp=cls.hist2_ts)

    def test_basic_serialization(self):
        """Test serialization of core OrderRecord fields."""
        serializer = OrderRecordSerializer(instance=self.order)
        data = serializer.data

        # Check a few key fields
        self.assertEqual(data['customer_name'], "Record Test")
        self.assertEqual(data['model'], "SE84UFO")
        self.assertEqual(data['status'], "ON_BENCH")
        self.assertEqual(data['quantity'], 1)
        self.assertEqual(data['order_date'], self.order_date.isoformat().replace('+00:00', 'Z'))
        self.assertIn('time_created', data)
        self.assertIn('time_updated', data)
        self.assertIn('options', data) # Should be included by default
        self.assertEqual(data['options'], 'No options') # Verify value as well

    def test_serialization_with_history(self):
        """Test serialization includes nested StatusHistory."""
        serializer = OrderRecordSerializer(instance=self.order)
        data = serializer.data

        self.assertIn('status_history', data)
        self.assertEqual(len(data['status_history']), 2)
        # History is ordered by timestamp descending by default
        self.assertEqual(data['status_history'][0]['new_status'], 'ON_BENCH')
        self.assertEqual(data['status_history'][0]['previous_status'], 'PARTS_PULLED')
        self.assertEqual(data['status_history'][0]['timestamp'], self.hist2_ts.isoformat().replace('+00:00', 'Z'))
        self.assertEqual(data['status_history'][1]['new_status'], 'PARTS_PULLED')
        self.assertEqual(data['status_history'][1]['previous_status'], 'NEW')
        self.assertEqual(data['status_history'][1]['timestamp'], self.hist1_ts.isoformat().replace('+00:00', 'Z'))

class StatusMetricsSerializerTests(TestCase):
    """Tests for the StatusMetricsSerializer."""
    def test_serialization(self):
        """Test that the serializer outputs the expected fields and values."""
        # Mock input data similar to what the view might provide
        mock_metrics_data = {
            'status': 'TESTING',
            'average_time_days': Decimal('10.5'),
            'sample_size': 20,
            'confidence_level': 'HIGH',
            'last_updated': timezone.now()
        }

        serializer = StatusMetricsSerializer(instance=mock_metrics_data)
        data = serializer.data

        self.assertEqual(len(data.keys()), 5) # Expecting 5 fields
        self.assertEqual(data['status'], 'TESTING')
        # Ensure field name and type (Decimal) are correct
        self.assertEqual(data['average_time_days'], Decimal('10.5'))
        self.assertEqual(data['sample_size'], 20)
        self.assertEqual(data['confidence_level'], 'HIGH')
        self.assertIn('last_updated', data) # Check presence and format
        self.assertIsNotNone(data['last_updated'])

    def test_serialization_with_nulls(self):
        """Test serialization when some metrics might be None."""
        mock_metrics_data = {
            'status': 'NEW',
            'average_time_days': None, # Example: No avg time calculated yet
            'sample_size': 0,
            'confidence_level': 'LOW',
            'last_updated': None
        }

        serializer = StatusMetricsSerializer(instance=mock_metrics_data)
        data = serializer.data

        self.assertEqual(data['status'], 'NEW')
        self.assertIsNone(data['average_time_days'])
        self.assertEqual(data['sample_size'], 0)
        self.assertEqual(data['confidence_level'], 'LOW')
        self.assertIsNone(data['last_updated'])
