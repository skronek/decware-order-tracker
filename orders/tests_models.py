from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import OrderRecord, StatusHistory

class OrderRecordModelTests(TestCase):
    """Tests for the OrderRecord model."""
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        cls.order = OrderRecord.objects.create(
            customer_name="Test Customer",
            origin="USA",
            model="TestModel",
            base="Std",
            volts="120",
            status="NEW"
        )

    def test_order_creation(self):
        """Test that an OrderRecord instance can be created."""
        self.assertIsInstance(self.order, OrderRecord)
        self.assertEqual(self.order.customer_name, "Test Customer")
        self.assertEqual(self.order.status, "NEW")
        # Check default timestamp is set
        self.assertIsNotNone(self.order.time_created)

    def test_order_str_representation(self):
        """Test the string representation of the OrderRecord model."""
        expected_str = f"{self.order.customer_name} - {self.order.model} ({self.order.status})"
        self.assertEqual(str(self.order), expected_str)

class StatusHistoryModelTests(TestCase):
    """Tests for the StatusHistory model."""
    @classmethod
    def setUpTestData(cls):
        # Create an OrderRecord for StatusHistory to link to
        cls.order = OrderRecord.objects.create(
            customer_name="History Test",
            origin="CAN",
            model="HistoryModel",
            status="INITIAL"
        )
        # Create a StatusHistory record
        cls.history_entry = StatusHistory.objects.create(
            order=cls.order,
            new_status="PROCESSING",
            previous_status="INITIAL"
        )

    def test_status_history_creation(self):
        """Test that a StatusHistory instance can be created and linked."""
        self.assertIsInstance(self.history_entry, StatusHistory)
        self.assertEqual(self.history_entry.order, self.order)
        self.assertEqual(self.history_entry.new_status, "PROCESSING")
        self.assertEqual(self.history_entry.previous_status, "INITIAL")
        self.assertIsNotNone(self.history_entry.timestamp)

    def test_status_history_default_change_date(self):
        """Test that timestamp defaults to the current time."""
        # Create a new entry without specifying timestamp
        now = timezone.now()
        new_entry = StatusHistory.objects.create(order=self.order, new_status="SHIPPED")
        # Allow for a small delta in time comparison
        time_difference = now - new_entry.timestamp
        self.assertTrue(abs(time_difference.total_seconds()) < 1)

    def test_status_history_str_representation(self):
        """Test the string representation of the StatusHistory model."""
        # Construct the expected string based on the actual __str__ method
        expected_str = f"{self.order.customer_name} - {self.history_entry.previous_status} → {self.history_entry.new_status}"
        self.assertEqual(str(self.history_entry), expected_str)

    def test_status_history_nullable_previous_status(self):
        """Test that previous_status can be null."""
        # Create an entry with no previous status (e.g., the very first status)
        first_entry = StatusHistory.objects.create(
            order=self.order,
            new_status="INITIAL",
            previous_status=None # Explicitly set to None
        )
        self.assertIsInstance(first_entry, StatusHistory)
        self.assertIsNone(first_entry.previous_status)

        # Also test creating without specifying it (should default to null if DB allows)
        another_order = OrderRecord.objects.create(customer_name="Another", status="FIRST")
        implicit_null_entry = StatusHistory.objects.create(
            order=another_order,
            new_status="FIRST"
            # previous_status is not provided
        )
        self.assertIsInstance(implicit_null_entry, StatusHistory)
        self.assertIsNone(implicit_null_entry.previous_status)
