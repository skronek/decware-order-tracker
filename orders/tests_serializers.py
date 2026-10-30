from django.test import TestCase
from django.utils import timezone
from .models import OrderEstimate, OrderRecord, StatusHistory
from .serializers import StatusHistorySerializer, OrderRecordSerializer
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

    def test_estimated_completion_from_stored_estimate(self):
        """estimated_completion comes from the stored OrderEstimate, with days_remaining from today."""
        today = timezone.localdate()
        OrderEstimate.objects.create(
            order=self.order,
            range_start_date=today + datetime.timedelta(days=15),
            estimated_date=today + datetime.timedelta(days=20),
            range_end_date=today + datetime.timedelta(days=30),
            queue_position=None,
            confidence_level="MEDIUM",
            explanation="Being built.",
            computed_at=timezone.now(),
        )
        order = OrderRecord.objects.get(pk=self.order.pk)
        est = OrderRecordSerializer(instance=order).data['estimated_completion']
        self.assertEqual(est['days_remaining'], 20)
        self.assertEqual(est['estimated_date'], (today + datetime.timedelta(days=20)).isoformat())
        self.assertEqual(est['range_start_date'], (today + datetime.timedelta(days=15)).isoformat())
        self.assertEqual(est['range_end_date'], (today + datetime.timedelta(days=30)).isoformat())
        self.assertEqual(est['confidence_level'], 'MEDIUM')
        self.assertEqual(est['explanation'], 'Being built.')

    def test_days_remaining_never_negative(self):
        today = timezone.localdate()
        OrderEstimate.objects.create(
            order=self.order,
            range_start_date=today - datetime.timedelta(days=5),
            estimated_date=today - datetime.timedelta(days=3),
            range_end_date=today,
            confidence_level="LOW",
            computed_at=timezone.now(),
        )
        order = OrderRecord.objects.get(pk=self.order.pk)
        self.assertEqual(OrderRecordSerializer(instance=order).data['estimated_completion']['days_remaining'], 0)

    def test_estimated_completion_without_estimate(self):
        """Orders without a stored estimate (e.g. finished ones) have no estimated_completion."""
        self.assertIsNone(OrderRecordSerializer(instance=self.order).data['estimated_completion'])
