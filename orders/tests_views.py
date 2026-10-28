from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import OrderRecord, StatusHistory

class OrderRecordViewSetTests(APITestCase):
    """Tests for the OrderRecordViewSet API endpoints."""
    @classmethod
    def setUpTestData(cls):
        cls.order1 = OrderRecord.objects.create(customer_name="View Test 1", model="VT1", status="NEW")
        cls.order2 = OrderRecord.objects.create(customer_name="View Test 2", model="VT2", status="TESTING")
        cls.list_url = reverse('orders:order-list') # Correct name based on basename='order'
        cls.detail_url = reverse('orders:order-detail', kwargs={'pk': cls.order1.pk})
        cls.non_existent_url = reverse('orders:order-detail', kwargs={'pk': 999})

    def test_list_orders(self):
        """Ensure we can list all order records."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) # Assuming pagination is enabled

    def test_retrieve_order(self):
        """Ensure we can retrieve a single order record by its id."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order1.pk)
        self.assertEqual(response.data['customer_name'], self.order1.customer_name)

    def test_retrieve_non_existent_order(self):
        """Ensure retrieving a non-existent order returns 404 Not Found."""
        response = self.client.get(self.non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_order_without_trailing_slash_redirects(self):
        """A detail URL missing its trailing slash redirects to the API, not the React page."""
        response = self.client.get(self.detail_url.rstrip('/'))
        self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)
        self.assertEqual(response['Location'], self.detail_url)

    def test_unknown_api_path_returns_404(self):
        """Unknown /api/ paths return 404 instead of falling through to the React page."""
        response = self.client.get('/api/orders/1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_customer_name(self):
        """Ensure filtering by customer_name works."""
        filter_url = f"{self.list_url}?customer_name={self.order1.customer_name}"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.order1.pk)

    def test_filter_by_model(self):
        """Ensure filtering by model works."""
        filter_url = f"{self.list_url}?model={self.order2.model}"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.order2.pk)

    def test_filter_by_status_case_insensitive(self):
        """Ensure filtering by status is case-insensitive ('iexact')."""
        # Test with lowercase 'testing'
        filter_url = f"{self.list_url}?status=testing"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.order2.pk)

        # Test with uppercase 'TESTING'
        filter_url_upper = f"{self.list_url}?status=TESTING"
        response_upper = self.client.get(filter_url_upper)
        self.assertEqual(response_upper.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_upper.data['results']), 1)
        self.assertEqual(response_upper.data['results'][0]['id'], self.order2.pk)

    def test_filter_no_results(self):
        """Ensure filtering with no matching criteria returns an empty list."""
        filter_url = f"{self.list_url}?model=NonExistentModel"
        response = self.client.get(filter_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

class OrderRecordFilteringAndOrderingTests(APITestCase):
    """Multi-field exact-match filtering and ordering on the order list."""
    @classmethod
    def setUpTestData(cls):
        cls.order1 = OrderRecord.objects.create(
            customer_name="Api Test User 1", origin="USA", model="UFO", base="Std", volts="120", status="NEW"
        )
        cls.order2 = OrderRecord.objects.create(
            customer_name="Api Test User 2", origin="CAN", model="SE84", base="Anniv", volts="240", status="ON_BENCH"
        )
        # Same details as order1, different status
        cls.order3 = OrderRecord.objects.create(
            customer_name="Api Test User 1", origin="USA", model="UFO", base="Std", volts="120", status="TESTING"
        )
        cls.list_url = reverse('orders:order-list')

    def test_filter_by_all_key_fields(self):
        params = {'customer_name': 'Api Test User 2', 'origin': 'CAN', 'model': 'SE84', 'base': 'Anniv', 'volts': '240'}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([r['id'] for r in response.data['results']], [self.order2.pk])

    def test_filter_by_key_fields_and_status(self):
        params = {'customer_name': 'Api Test User 1', 'origin': 'USA', 'model': 'UFO', 'base': 'Std', 'volts': '120'}
        response = self.client.get(self.list_url, {**params, 'status': 'TESTING'})
        self.assertEqual([r['id'] for r in response.data['results']], [self.order3.pk])
        response = self.client.get(self.list_url, {**params, 'status': 'NEW'})
        self.assertEqual([r['id'] for r in response.data['results']], [self.order1.pk])

    def test_filter_by_key_fields_not_found(self):
        params = {'customer_name': 'NonExistent', 'origin': 'XXX', 'model': 'YYY', 'base': 'ZZZ', 'volts': '000'}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_ordering_by_time_created(self):
        response = self.client.get(self.list_url, {'ordering': 'time_created'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [r['id'] for r in response.data['results']],
            [self.order1.pk, self.order2.pk, self.order3.pk],
        )

class StatusHistoryViewSetTests(APITestCase):
    """Tests for the StatusHistoryViewSet API endpoints."""

    @classmethod
    def setUpTestData(cls):
        # Create an order to associate history with
        cls.order = OrderRecord.objects.create(
            customer_name="History Test",
            model="HT1",
            status="TESTING"
        )

        # Create some history records
        cls.history1 = StatusHistory.objects.create(
            order=cls.order,
            previous_status="ON_BENCH",
            new_status="TESTING"
        )
        cls.history2 = StatusHistory.objects.create(
            order=cls.order,
            previous_status="NEW",
            new_status="ON_BENCH"
        )

        # Define URLs
        cls.list_url = reverse('orders:history-list')
        cls.detail_url = reverse('orders:history-detail', kwargs={'pk': cls.history1.pk})
        cls.non_existent_url = reverse('orders:history-detail', kwargs={'pk': 999})

    def test_list_history(self):
        """Ensure we can list all status history records."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check count for pagination
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_history(self):
        """Ensure we can retrieve a single status history record."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.history1.pk)
        self.assertEqual(response.data['previous_status'], self.history1.previous_status)
        self.assertEqual(response.data['new_status'], self.history1.new_status)
        # Check that the related order pk matches
        self.assertEqual(response.data['order'], self.order.pk)

    def test_retrieve_non_existent_history(self):
        """Ensure retrieving a non-existent history record returns 404 Not Found."""
        response = self.client.get(self.non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
