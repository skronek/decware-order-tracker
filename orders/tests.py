from django.test import TestCase
from .models import OrderEstimate, OrderRecord, StatusHistory, StatusMetrics
from .serializers import OrderRecordSerializer, StatusHistorySerializer, StatusMetricsSerializer
from rest_framework.test import APITestCase
from rest_framework import status as http_status
from django.utils import timezone
from django.urls import reverse

# Create your tests here.

class OrderRecordModelTests(TestCase):
    def test_create_order_record(self):
        """Test creating a basic OrderRecord instance."""
        order = OrderRecord.objects.create(
            customer_name="Test Customer",
            origin="USA",
            model="UFO",
            base="Standard",
            volts="120V",
            quantity=1,
            status="NEW"
        )
        self.assertIsInstance(order, OrderRecord)
        self.assertEqual(str(order), "Test Customer - UFO (NEW)") # Updated expected string
        self.assertEqual(order.customer_name, "Test Customer")
        self.assertEqual(order.status, "NEW")

    def test_create_status_history(self):
        """Test creating a StatusHistory instance linked to an OrderRecord."""
        # 1. Create an OrderRecord first
        order = OrderRecord.objects.create(
            customer_name="History Tester",
            origin="CAN",
            model="SE84UFO",
            base="Anniversary",
            volts="240V",
            quantity=2,
            status="NEW"
        )

        # 2. Create a StatusHistory record for this order
        status_update_time = timezone.now()
        history = StatusHistory.objects.create(
            order=order,
            new_status="IN_PROGRESS",
            previous_status="NEW",
            timestamp=status_update_time
        )

        # 3. Assertions
        self.assertIsInstance(history, StatusHistory)
        self.assertEqual(history.order, order)
        self.assertEqual(history.new_status, "IN_PROGRESS")
        self.assertEqual(history.previous_status, "NEW")
        self.assertEqual(history.timestamp, status_update_time)
        self.assertEqual(str(history), f"{order.customer_name} - {history.previous_status} → {history.new_status}")


class OrderRecordSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up non-modified objects used by all test methods."""
        # Set TESTING flag
        from django.conf import settings
        setattr(settings, 'TESTING', True)
        
        # Create test order
        cls.order1 = OrderRecord.objects.create(
            customer_name="Test Customer", model="TEST", base="B", volts="V", status='PARTS_PULLED'
        )
        
        # Create status history
        cls.history1_time = timezone.now() - timezone.timedelta(days=5)
        cls.history1 = StatusHistory.objects.create(
            order=cls.order1, 
            previous_status="NEW", 
            new_status="PARTS_PULLED",
            timestamp=cls.history1_time
        )
        
        # Create stored estimate
        cls.estimate1 = OrderEstimate.objects.create(
            order=cls.order1,
            estimated_date=timezone.localdate() + timezone.timedelta(days=20),
            range_end_date=timezone.localdate() + timezone.timedelta(days=30),
            confidence_level="MEDIUM",
            computed_at=timezone.now(),
        )

    def tearDown(self):
        """Clean up after tests."""
        # Reset TESTING flag
        from django.conf import settings
        setattr(settings, 'TESTING', False)

    def test_order_record_serialization(self):
        """Test serializing an OrderRecord instance."""
        serializer = OrderRecordSerializer(instance=self.order1)
        data = serializer.data

        # Expected data based on setUpTestData
        expected_days_remaining = 20  # From the stored estimate
        expected_confidence = 'MEDIUM'

        # --- Assert Basic Fields ---
        self.assertEqual(data['id'], self.order1.id)
        self.assertEqual(data['customer_name'], "Test Customer")
        self.assertEqual(data['model'], "TEST")
        self.assertEqual(data['status'], "PARTS_PULLED")
        self.assertTrue('time_created' in data)
        self.assertTrue('time_updated' in data)
        # Order date might be None or auto-populated in test environment
        # self.assertEqual(data['order_date'], None)  # No order_date set in setUpTestData

        # --- Assert Nested Status History ---
        self.assertEqual(len(data['status_history']), 1)
        history_data = data['status_history'][0]
        self.assertEqual(history_data['previous_status'], "NEW")
        self.assertEqual(history_data['new_status'], "PARTS_PULLED")
        self.assertEqual(history_data['timestamp'], self.history1_time.isoformat().replace('+00:00', 'Z'))

        # --- Assert Calculated Estimated Completion ---
        self.assertIsNotNone(data['estimated_completion'])
        est_completion = data['estimated_completion']
        self.assertEqual(est_completion['days_remaining'], expected_days_remaining)
        self.assertEqual(est_completion['confidence_level'], expected_confidence)
        self.assertIn('explanation', est_completion)

    def test_estimated_completion_without_estimate(self):
        """Orders without a stored estimate (e.g. finished ones) have no estimated_completion."""
        finished = OrderRecord.objects.create(
            customer_name="Final Status Test", model="FINAL", base="B", volts="V", status='PASSED_QC'
        )
        data = OrderRecordSerializer(instance=finished).data
        self.assertIsNone(data['estimated_completion'])


class StatusHistorySerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up a StatusHistory instance."""
        order = OrderRecord.objects.create(customer_name="Hist Ser Test", model="HST", status="NEW")
        cls.timestamp = timezone.now()
        cls.history = StatusHistory.objects.create(
            order=order,
            previous_status="NEW",
            new_status="PARTS_PULLED",
            timestamp=cls.timestamp
        )

    def test_status_history_serialization(self):
        """Test serializing a StatusHistory instance."""
        serializer = StatusHistorySerializer(instance=self.history)
        data = serializer.data

        self.assertEqual(len(data), 6) # Expect 6 fields: id, order, previous_status, new_status, timestamp, is_observed
        self.assertEqual(data['previous_status'], "NEW")
        self.assertEqual(data['new_status'], "PARTS_PULLED")
        self.assertEqual(data['timestamp'], self.timestamp.isoformat().replace('+00:00', 'Z'))
        self.assertIn('id', data) # Verify id field exists
        self.assertIn('order', data) # Verify order field exists


class StatusMetricsSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up a StatusMetrics instance."""
        cls.metrics = StatusMetrics.objects.create(
            status='TESTING',
            average_time_days=4.2,
            sample_size=25,
            confidence_level='HIGH'
        )

    def test_status_metrics_serialization(self):
        """Test serializing a StatusMetrics instance."""
        serializer = StatusMetricsSerializer(instance=self.metrics)
        data = serializer.data

        self.assertEqual(len(data), 5) # Expect 5 fields
        self.assertEqual(data['status'], 'TESTING')
        self.assertEqual(data['average_time_days'], 4.2)
        self.assertEqual(data['sample_size'], 25)
        self.assertEqual(data['confidence_level'], 'HIGH')
        self.assertTrue('last_updated' in data) # Just check it exists


# --- API ViewSet Tests ---
class OrderRecordViewSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up data for API tests."""
        # Create multiple orders with different statuses and details
        cls.order1 = OrderRecord.objects.create(
            customer_name="Api Test User 1", origin="USA", model="UFO", base="Std", volts="120", status="NEW"
        )
        cls.order2 = OrderRecord.objects.create(
            customer_name="Api Test User 2", origin="CAN", model="SE84", base="Anniv", volts="240", status="ON_BENCH"
        )
        cls.order3 = OrderRecord.objects.create(
            customer_name="Api Test User 1", origin="USA", model="UFO", base="Std", volts="120", status="TESTING" # Same details as order1, different status
        )
        cls.order4 = OrderRecord.objects.create(
            customer_name="Api Test User 3", origin="EU", model="TORII", base="MK5", volts="230", status="NEW"
        )

        # Base URL for the viewset
        cls.list_url = "/api/orders/orders/" # Correct URL based on urls.py includes

    def test_list_orders(self):
        """Ensure we can list all order records."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4) # Expecting a plain list

    def test_retrieve_order(self):
        """Ensure we can retrieve a specific order record by its ID."""
        detail_url = f"{self.list_url}{self.order2.pk}/"
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order2.pk)
        self.assertEqual(response.data['customer_name'], "Api Test User 2")
        self.assertEqual(response.data['status'], "ON_BENCH")

    def test_filter_by_status(self):
        """Ensure we can filter orders by status."""
        filter_url = f"{self.list_url}?status=NEW"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertTrue(all(item['status'] == 'NEW' for item in results))
        # Check IDs to be sure
        result_ids = {item['id'] for item in results}
        self.assertEqual(result_ids, {self.order1.pk, self.order4.pk})

    def test_filter_by_exact_match_found(self):
        """Ensure we can filter for an exact order match (found)."""
        filter_url = f"{self.list_url}?customer_name=Api Test User 2&origin=CAN&model=SE84&base=Anniv&volts=240"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.order2.pk)

    def test_filter_by_exact_match_not_found(self):
        """Ensure exact match filter returns empty list if no match."""
        filter_url = f"{self.list_url}?customer_name=NonExistent&origin=XXX&model=YYY&base=ZZZ&volts=000"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(len(response.data['results']), 0)

    def test_filter_by_exact_match_and_status_found(self):
        """Ensure we can filter by exact match AND status (found order3)."""
        # Target order3 which has same details as order1 but different status
        filter_url = f"{self.list_url}?customer_name=Api Test User 1&origin=USA&model=UFO&base=Std&volts=120&status=TESTING"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.order3.pk)
        self.assertEqual(results[0]['status'], 'TESTING')

    def test_filter_by_exact_match_for_status_order1(self):
        """Ensure filter by exact match AND specific status returns correct record (order1)."""
        # Test case: All fields match order1, including status 'NEW'
        params = {'customer_name': 'Api Test User 1', 'origin': 'USA', 'model': 'UFO', 'base': 'Std', 'volts': '120', 'status': 'NEW'}
        url_path = reverse('orders:order-list') # Correct view name with namespace
        response = self.client.get(url_path, params)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        results = response.data['results']
        # This query exactly matches order1, so we expect 1 result.
        self.assertEqual(len(results), 1)
        # Verify it is indeed order1
        self.assertEqual(results[0]['id'], self.order1.pk)
        self.assertEqual(results[0]['customer_name'], 'Api Test User 1')
        self.assertEqual(results[0]['model'], 'UFO')
        self.assertEqual(results[0]['status'], 'NEW')

    def test_ordering(self):
        """Test ordering by time_created."""
        # Default is -time_updated, let's test time_created
        filter_url = f"{self.list_url}?ordering=time_created"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        results = response.data['results'] # Access the list within paginated response
        self.assertEqual(len(results), 4)
        # Check if IDs are in ascending order (matching creation order)
        result_ids = [item['id'] for item in results]
        self.assertEqual(result_ids, [self.order1.pk, self.order2.pk, self.order3.pk, self.order4.pk])
