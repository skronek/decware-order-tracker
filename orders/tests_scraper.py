"""
Unit tests for the CSV parsing and database update logic in orders/scraper.py.
"""

import os
import shutil
import tempfile
import datetime
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from .models import OrderRecord, StatusHistory
from .scraper import DecwareOrderScraper

HEADER = 'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time\r\n'


class ScraperParseCsvTests(TestCase):
    """Tests parse_csv against real CSV files."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        self.scraper = DecwareOrderScraper()

    def _write(self, content, encoding='utf-8'):
        path = os.path.join(self.test_dir, 'orders.csv')
        with open(path, 'w', encoding=encoding, newline='') as f:
            f.write(content)
        return path

    def test_parse_valid_csv(self):
        path = self._write(
            HEADER
            + '"Ann","Web","2","SE84UFO","Walnut","120V","Tubes","Parts Pulled","2024-07-31 10:00:00"\r\n'
            + '"Bob","Mail","x","Torii","","240V","","On Bench","2024-08-01 11:30:00"\r\n'
        )

        orders = self.scraper.parse_csv(path)

        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0], {
            'customer_name': 'Ann', 'origin': 'Web', 'quantity': 2, 'model': 'SE84UFO', 'base': 'Walnut',
            'volts': '120V', 'options': 'Tubes', 'status': 'PARTS_PULLED',
            'order_date': timezone.make_aware(datetime.datetime(2024, 7, 31, 10, 0, 0)),
        })
        self.assertEqual(orders[1]['quantity'], 1)  # Non-numeric Qty defaults to 1
        self.assertEqual(orders[1]['status'], 'ON_BENCH')
        self.assertEqual(orders[1]['base'], '')

    def test_parse_csv_with_bom_and_extra_columns(self):
        path = self._write(
            'For,From,Qty,MODEL,Base,VOLTS,Options,Status,Date-Time,Extra\r\n'
            '"Ann","Web","1","M","B","120V","","New","2024-07-31 10:00:00","ignored"\r\n',
            encoding='utf-8-sig',
        )

        orders = self.scraper.parse_csv(path)

        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['customer_name'], 'Ann')
        self.assertNotIn('Extra', orders[0])

    def test_parse_latin1_csv(self):
        path = self._write(
            HEADER + '"Jos\xe9","Web","1","M","B","120V","","New","2024-07-31 10:00:00"\r\n',
            encoding='latin-1',
        )

        orders = self.scraper.parse_csv(path)

        self.assertEqual([o['customer_name'] for o in orders], ['Jos\xe9'])

    def test_status_normalization(self):
        statuses = ['', 'New', 'parts pulled', 'Passed QC', 'Passed Quality Control - Awaiting Payment',
                    'Completed waiting for wood base']
        path = self._write(HEADER + ''.join(
            f'"C{i}","Web","1","M","B","120V","","{s}","2024-07-31 10:00:00"\r\n' for i, s in enumerate(statuses)
        ))

        orders = self.scraper.parse_csv(path)

        self.assertEqual([o['status'] for o in orders], [
            'NEW', 'NEW', 'PARTS_PULLED', 'PASSED_QC', 'PASSED_QC_AWAITING_PAYMENT', 'COMPLETED_WAITING_BASE',
        ])

    def test_unknown_status_is_logged_and_left_unset(self):
        path = self._write(HEADER + '"Ann","Web","1","M","B","120V","","Shipped","2024-07-31 10:00:00"\r\n')

        with self.assertLogs('orders.scraper', level='WARNING') as logs:
            orders = self.scraper.parse_csv(path)

        self.assertIsNone(orders[0]['status'])
        self.assertTrue(any("Unknown status 'Shipped'" in line for line in logs.output))

    def test_rows_with_bad_dates_are_skipped(self):
        path = self._write(
            HEADER
            + '"Good","Web","1","M","B","120V","","New","2024-07-31 10:00:00"\r\n'
            + '"Bad","Web","1","M","B","120V","","New","not a date"\r\n'
            + '"Empty","Web","1","M","B","120V","","New",""\r\n'
        )

        orders = self.scraper.parse_csv(path)

        self.assertEqual([o['customer_name'] for o in orders], ['Good'])

    def test_missing_required_column_returns_nothing(self):
        path = self._write('For,From,MODEL\r\n"Ann","Web","M"\r\n')

        self.assertEqual(self.scraper.parse_csv(path), [])

    def test_parse_empty_csv(self):
        self.assertEqual(self.scraper.parse_csv(self._write(HEADER)), [])

    def test_parse_csv_io_error(self):
        self.assertEqual(self.scraper.parse_csv(os.path.join(self.test_dir, 'non_existent.csv')), [])


class ScraperUpdateDatabaseTests(TestCase):
    """Tests the update_database method of the DecwareOrderScraper."""

    def setUp(self):
        """Set up a scraper instance for database tests."""
        self.scraper = DecwareOrderScraper()

    def test_update_db_create_new_orders(self):
        """Test creating new orders in the database."""
        parsed_orders = [
            {'customer_name': 'New Cust 1', 'origin': 'Web', 'quantity': 1, 'model': 'M_NEW1', 'base': 'B1', 'volts': 'V1', 'options': 'O1', 'status': 'NEW', 'order_date': timezone.make_aware(datetime.datetime(2023, 1, 1))},
            {'customer_name': 'New Cust 2', 'origin': 'Mail','quantity': 2, 'model': 'M_NEW2', 'base': 'B2', 'volts': 'V2', 'options': 'O2', 'status': 'PARTS_PULLED', 'order_date': timezone.make_aware(datetime.datetime(2023, 1, 2))}
        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 2)
        self.assertEqual(OrderRecord.objects.count(), 2)
        self.assertEqual(StatusHistory.objects.count(), 2)

        # Check Order 1 details
        order1 = OrderRecord.objects.get(customer_name='New Cust 1')
        self.assertEqual(order1.status, 'NEW')
        self.assertEqual(order1.quantity, 1)
        history1 = StatusHistory.objects.get(order=order1)
        self.assertIsNone(history1.previous_status)
        self.assertEqual(history1.new_status, 'NEW')

        # Check Order 2 details
        order2 = OrderRecord.objects.get(customer_name='New Cust 2')
        self.assertEqual(order2.status, 'PARTS_PULLED')
        self.assertEqual(order2.quantity, 2)
        history2 = StatusHistory.objects.get(order=order2)
        self.assertIsNone(history2.previous_status)
        self.assertEqual(history2.new_status, 'PARTS_PULLED')

    def test_update_db_update_existing_orders_no_status_change(self):
        """Test updating existing orders without status change (no history created)."""
        # Create initial order
        order = OrderRecord.objects.create(
            customer_name='Existing Cust', origin='Web', quantity=1, model='M_EXIST',
            base='Wood', volts='120V', options='Old', status='ON_BENCH',
            order_date=timezone.make_aware(datetime.datetime(2023, 12, 1))
        )
        parsed_orders = [
            { # Match the existing order
                'customer_name': 'Existing Cust', 'origin': 'Web', 'model': 'M_EXIST',
                'base': 'Wood', 'volts': '120V', # Composite key match
                'quantity': 3, 'options': 'Updated', 'status': 'ON_BENCH',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 15))
            }
        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 1)
        self.assertEqual(OrderRecord.objects.count(), 1)
        # Status history should NOT increase
        self.assertEqual(StatusHistory.objects.count(), 0)

        updated_order = OrderRecord.objects.get(pk=order.pk)
        self.assertEqual(updated_order.quantity, 3)
        self.assertEqual(updated_order.options, 'Updated')
        self.assertEqual(updated_order.order_date, timezone.make_aware(datetime.datetime(2023, 12, 15)))
        self.assertEqual(updated_order.status, 'ON_BENCH')

    def test_update_db_update_existing_orders_with_status_change(self):
        """Test updating existing orders WITH a status change (history created)."""
        # Create an initial order
        initial_status = 'ON_BENCH'
        order = OrderRecord.objects.create(
            customer_name='Existing Cust', origin='Web', quantity=1, model='M_EXIST',
            base='Wood', volts='120V', options='Old', status=initial_status,
            order_date=timezone.make_aware(datetime.datetime(2023, 12, 1))
        )
        parsed_orders = [
            { # Match the existing order
                'customer_name': 'Existing Cust', 'origin': 'Web', 'model': 'M_EXIST',
                'base': 'Wood', 'volts': '120V',
                # Update status
                'quantity': 1, 'options': 'Old', 'status': 'TESTING',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 1))
            }
        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 1)
        self.assertEqual(OrderRecord.objects.count(), 1)
        # Status history SHOULD increase
        self.assertEqual(StatusHistory.objects.count(), 1)

        updated_order = OrderRecord.objects.get(pk=order.pk)
        self.assertEqual(updated_order.status, 'TESTING')

        # Check the new history entry
        latest_history = StatusHistory.objects.filter(order=updated_order).latest('timestamp')
        self.assertEqual(latest_history.previous_status, 'ON_BENCH')
        self.assertEqual(latest_history.new_status, 'TESTING')

    def test_update_db_mixed_create_and_update(self):
        """Test a batch containing both new orders and updates."""
        # Existing order
        existing_order = OrderRecord.objects.create(
            customer_name='Existing Cust', origin='Web', quantity=1, model='M_EXIST',
            base='Wood', volts='120V', options='Old', status='NEW',
            order_date=timezone.make_aware(datetime.datetime(2023, 12, 1))
        )
        parsed_orders = [
            # Update existing order (change status)
            {
                'customer_name': 'Existing Cust', 'origin': 'Web', 'model': 'M_EXIST',
                'base': 'Wood', 'volts': '120V', # Composite key match
                'quantity': 2, 'options': 'Updated', 'status': 'PARTS_PULLED',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 1))
            },
            # Create new order
            {
                'customer_name': 'New Cust', 'origin': 'Mail', 'quantity': 1, 'model': 'M_NEW',
                'base': 'Plastic', 'volts': '240V', 'options': 'None', 'status': 'NEW',
                'order_date': timezone.make_aware(datetime.datetime(2023, 12, 15))
            },

        ]

        orders_processed = self.scraper.update_database(parsed_orders)

        self.assertEqual(orders_processed, 2)
        self.assertEqual(OrderRecord.objects.count(), 2)
        # 1 initial + 1 status change + 1 new order = 2 history entries
        self.assertEqual(StatusHistory.objects.count(), 2)

        updated_mixed = OrderRecord.objects.get(pk=existing_order.pk)
        self.assertEqual(updated_mixed.status, 'PARTS_PULLED')
        self.assertEqual(updated_mixed.quantity, 2)
        self.assertEqual(updated_mixed.options, 'Updated')

        new_other = OrderRecord.objects.get(customer_name='New Cust')
        self.assertEqual(new_other.status, 'NEW')

        # Check history counts per order
        self.assertEqual(StatusHistory.objects.filter(order=updated_mixed).count(), 1)
        self.assertEqual(StatusHistory.objects.filter(order=new_other).count(), 1)

    @patch('orders.scraper.logger.error')
    def test_update_db_handles_exception(self, mock_logger_error):
        """A database error on one order doesn't stop the others (each order gets a savepoint)."""
        good = self._row('Good Cust')
        # quantity is a PositiveIntegerField, so the database's CHECK constraint rejects -1
        bad = {**self._row('Bad Cust'), 'quantity': -1}
        good2 = self._row('Good Cust 2')

        orders_processed = self.scraper.update_database([good, bad, good2])

        self.assertEqual(orders_processed, 2)
        self.assertEqual(
            set(OrderRecord.objects.values_list('customer_name', flat=True)), {'Good Cust', 'Good Cust 2'}
        )
        self.assertEqual(StatusHistory.objects.count(), 2)
        mock_logger_error.assert_called()
        self.assertIn("'customer_name': 'Bad Cust'", mock_logger_error.call_args[0][0])

    def test_duplicate_rows_keep_the_first(self):
        """A key that appears twice in one CSV is only applied once, without flip-flopping status."""
        order = OrderRecord.objects.create(
            customer_name='Dup', origin='Web', model='M', base='B', volts='120V', status='NEW',
            order_date=timezone.make_aware(datetime.datetime(2023, 1, 1)),
        )

        with self.assertLogs('orders.scraper', level='WARNING') as logs:
            processed = self.scraper.update_database([self._row('Dup', 'ON_BENCH'), self._row('Dup', 'NEW')])

        self.assertEqual(processed, 1)
        order.refresh_from_db()
        self.assertEqual(order.status, 'ON_BENCH')
        self.assertEqual(
            list(StatusHistory.objects.values_list('previous_status', 'new_status')), [('NEW', 'ON_BENCH')]
        )
        self.assertTrue(any('duplicate' in line for line in logs.output))

    def test_unknown_status_keeps_existing_status(self):
        """An unrecognized status (None from parsing) leaves the order's status alone but still marks it seen."""
        order = OrderRecord.objects.create(
            customer_name='Odd', origin='Web', model='M', base='B', volts='120V', status='ON_BENCH',
            order_date=timezone.make_aware(datetime.datetime(2023, 1, 1)),
        )

        processed = self.scraper.update_database([self._row('Odd', None), self._row('Brand New Odd', None)])

        self.assertEqual(processed, 1)
        order.refresh_from_db()
        self.assertEqual(order.status, 'ON_BENCH')
        self.assertIsNotNone(order.last_seen_at)
        self.assertIsNone(order.removed_at)
        self.assertFalse(StatusHistory.objects.exists())
        self.assertFalse(OrderRecord.objects.filter(customer_name='Brand New Odd').exists())

    def _row(self, name, status='NEW'):
        return {
            'customer_name': name, 'origin': 'Web', 'model': 'M', 'base': 'B', 'volts': '120V',
            'quantity': 1, 'options': '', 'status': status,
            'order_date': timezone.make_aware(datetime.datetime(2023, 1, 1)),
        }


class ScraperLifecycleTrackingTests(TestCase):
    """Tests last-seen/removed tracking and observed status changes in update_database."""

    def setUp(self):
        self.scraper = DecwareOrderScraper()

    def _create_order(self, name, status='NEW', last_seen_days_ago=1):
        return OrderRecord.objects.create(
            customer_name=name, origin='Web', model='M', base='B', volts='120V', status=status,
            order_date=timezone.make_aware(datetime.datetime(2023, 1, 1)),
            last_seen_at=timezone.now() - datetime.timedelta(days=last_seen_days_ago),
        )

    def _row(self, name, status='NEW'):
        return {
            'customer_name': name, 'origin': 'Web', 'model': 'M', 'base': 'B', 'volts': '120V',
            'quantity': 1, 'options': '', 'status': status,
            'order_date': timezone.make_aware(datetime.datetime(2023, 1, 1)),
        }

    def test_orders_in_csv_get_last_seen_and_missing_orders_get_removed(self):
        kept = self._create_order('Kept')
        gone = self._create_order('Gone')

        self.scraper.update_database([self._row('Kept')])

        kept.refresh_from_db()
        gone.refresh_from_db()
        self.assertGreater(kept.last_seen_at, timezone.now() - datetime.timedelta(minutes=1))
        self.assertIsNone(kept.removed_at)
        self.assertIsNotNone(gone.removed_at)
        self.assertLess(gone.last_seen_at, gone.removed_at)

    def test_reappearing_order_is_no_longer_removed(self):
        order = self._create_order('Back')
        order.removed_at = timezone.now() - datetime.timedelta(days=1)
        order.save()

        self.scraper.update_database([self._row('Back')])

        order.refresh_from_db()
        self.assertIsNone(order.removed_at)

    def test_partial_csv_does_not_mark_removals(self):
        for i in range(4):
            self._create_order(f'Active {i}')

        self.scraper.update_database([self._row('Active 0')])

        self.assertFalse(OrderRecord.objects.filter(removed_at__isnull=False).exists())

    def test_status_change_after_recent_run_is_observed(self):
        self._create_order('Steady', last_seen_days_ago=1)

        self.scraper.update_database([self._row('Steady', status='ON_BENCH')])

        change = StatusHistory.objects.get(previous_status='NEW')
        self.assertTrue(change.is_observed)

    def test_status_change_after_missed_runs_is_unobserved(self):
        self._create_order('Gap', last_seen_days_ago=30)

        self.scraper.update_database([self._row('Gap', status='ON_BENCH')])

        change = StatusHistory.objects.get(previous_status='NEW')
        self.assertFalse(change.is_observed)

    def test_initial_status_is_unobserved(self):
        self.scraper.update_database([self._row('Brand New')])

        self.assertFalse(StatusHistory.objects.get().is_observed)

# ==================================
# Integration Tests (Mocking the browser)
# ==================================

class ScraperRunTests(TestCase):
    """Runs download -> parse -> update with a fake browser that 'downloads' a CSV."""

    CSV = (
        HEADER
        + '"Integration User","Web","1","INT-MOD-A","Base-A","120V","Opt-A","New","2024-07-31 10:00:00"\r\n'
        + '"Another User","Mail","2","INT-MOD-B","Base-B","240V","Opt-B","Parts Pulled","2024-07-31 11:30:00"\r\n'
    )

    def _fake_driver(self, scraper):
        driver = MagicMock()
        button = MagicMock()

        def click():
            with open(os.path.join(scraper.download_dir, 'orders.csv'), 'w', encoding='utf-8-sig') as f:
                f.write(self.CSV)

        button.click.side_effect = click
        driver.find_elements.return_value = [button]
        return driver

    @patch('orders.scraper.time.sleep')
    @patch('orders.scraper.WebDriverWait')
    def test_run_downloads_parses_and_updates(self, mock_wait, mock_sleep):
        scraper = DecwareOrderScraper()
        driver = self._fake_driver(scraper)

        with patch.object(DecwareOrderScraper, '_init_driver', return_value=driver):
            self.assertTrue(scraper.run())

        driver.quit.assert_called_once()
        self.assertEqual(
            dict(OrderRecord.objects.values_list('customer_name', 'status')),
            {'Integration User': 'NEW', 'Another User': 'PARTS_PULLED'},
        )
        # The temporary download directory is removed
        self.assertIsNone(scraper.download_dir)

    def test_run_fails_and_cleans_up_when_driver_unavailable(self):
        scraper = DecwareOrderScraper()

        with patch.object(DecwareOrderScraper, '_init_driver', return_value=None):
            self.assertFalse(scraper.run())

        self.assertIsNone(scraper.download_dir)

    def test_driver_never_launches_in_tests(self):
        with self.assertRaises(RuntimeError):
            DecwareOrderScraper()._init_driver()
