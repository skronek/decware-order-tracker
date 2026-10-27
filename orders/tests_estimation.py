"""
Unit tests for the completion estimates in orders/estimation.py.
"""
import datetime

from django.test import TestCase
from django.utils import timezone

from .estimation import DEFAULT_BUILD_DAYS, SLOW_RATE_FACTOR, backtest, compute_estimates, estimate_orders
from .models import OrderEstimate, OrderRecord, StatusHistory

DAY = datetime.timedelta(days=1)


class EstimationTests(TestCase):
    """A shop that started 2 orders a week for the past 10 weeks, with 3 orders waiting."""

    def setUp(self):
        self.now = timezone.now()
        self.first_run = self.now - 70 * DAY
        # Two orders leave NEW each week, both seen by daily runs
        for week in range(10):
            for i in range(2):
                left_new = self.first_run + (week * 7 + 3) * DAY
                order = self._order(f'Built {week}-{i}', 'ON_BENCH', order_day=week * 2 + i,
                                    removed_at=left_new + 2 * DAY)
                self._history(order, None, 'NEW', self.first_run, observed=False)
                self._history(order, 'NEW', 'ON_BENCH', left_new)
        self.waiting = [self._order(f'Waiting {i}', 'NEW', order_day=100 + i) for i in range(3)]
        for order in self.waiting:
            self._history(order, None, 'NEW', self.first_run, observed=False)

    def _order(self, name, status, order_day, removed_at=None):
        return OrderRecord.objects.create(
            customer_name=name, origin='', model='M', volts='', status=status,
            order_date=timezone.make_aware(datetime.datetime(2023, 1, 1)) + order_day * DAY,
            time_created=self.first_run,
            last_seen_at=(removed_at - DAY) if removed_at else self.now,
            removed_at=removed_at,
        )

    def _history(self, order, previous, new, when, observed=True):
        StatusHistory.objects.create(order=order, previous_status=previous, new_status=new,
                                     timestamp=when, is_observed=observed)

    def _estimates(self):
        model, estimates = estimate_orders(self.now)
        return model, {e.order.customer_name: e for e in estimates}

    def test_start_rate_counts_orders_leaving_new(self):
        model, _ = self._estimates()
        self.assertAlmostEqual(model.starts_per_week, 2.0, places=1)
        self.assertEqual(model.precise_starts, 20)

    def test_waiting_orders_are_estimated_in_queue_order(self):
        model, estimates = self._estimates()
        typical_build, late_build = DEFAULT_BUILD_DAYS
        for position, order in enumerate(self.waiting):
            estimate = estimates[order.customer_name]
            weeks = (position + 1) / model.starts_per_week
            self.assertEqual(estimate.queue_position, position)
            self.assertEqual(estimate.estimated_date, (self.now + (weeks * 7 + typical_build) * DAY).date())
            self.assertEqual(estimate.range_end_date,
                             (self.now + (weeks / SLOW_RATE_FACTOR * 7 + late_build) * DAY).date())

    def test_order_being_built_gets_remaining_build_time(self):
        order = self._order('On bench', 'ON_BENCH', order_day=50)
        self._history(order, None, 'NEW', self.first_run, observed=False)
        self._history(order, 'NEW', 'ON_BENCH', self.now - 5 * DAY)

        _, estimates = self._estimates()

        estimate = estimates['On bench']
        self.assertIsNone(estimate.queue_position)
        self.assertEqual(estimate.estimated_date, (self.now + (DEFAULT_BUILD_DAYS[0] - 5) * DAY).date())

    def test_finished_orders_are_not_estimated(self):
        passed = self._order('Passed', 'PASSED_QC', order_day=60)
        self._history(passed, None, 'PASSED_QC', self.first_run, observed=False)

        _, estimates = self._estimates()

        self.assertNotIn('Passed', estimates)
        self.assertFalse(any(name.startswith('Built 0') for name in estimates))  # Removed long ago

    def test_starts_during_a_gap_are_spread_over_it(self):
        # Ten orders that dropped off while NEW sometime in a 10-week gap: one start per week
        for i in range(10):
            self._order(f'Gap {i}', 'NEW', order_day=80 + i, removed_at=self.now - DAY)
            OrderRecord.objects.filter(customer_name=f'Gap {i}').update(last_seen_at=self.first_run)

        model, _ = self._estimates()

        self.assertAlmostEqual(model.starts_per_week, 3.0, places=1)
        self.assertEqual(model.precise_starts, 20)

    def test_confidence_is_low_without_observed_builds(self):
        _, estimates = self._estimates()
        self.assertTrue(all(e.confidence_level == 'LOW' for e in estimates.values()))

    def test_observed_builds_set_build_time(self):
        for i in range(5):
            order = self._order(f'Done {i}', 'PASSED_QC', order_day=70 + i)
            self._history(order, None, 'NEW', self.first_run, observed=False)
            self._history(order, 'NEW', 'ON_BENCH', self.now - 30 * DAY)
            self._history(order, 'ON_BENCH', 'PASSED_QC', self.now - (30 - 10 - i) * DAY)

        model, estimates = self._estimates()

        self.assertEqual(model.build_samples, 5)
        self.assertAlmostEqual(model.build_typical_days, 12.0)
        self.assertEqual(estimates['Waiting 0'].confidence_level, 'MEDIUM')

    def test_compute_estimates_replaces_stored_estimates(self):
        compute_estimates()
        compute_estimates()
        self.assertEqual(OrderEstimate.objects.count(), 3)

    def test_backtest_compares_with_what_happened(self):
        result = backtest(self.now - 35 * DAY, now=self.now)
        self.assertEqual(result['actual_starts'], 10)
        self.assertAlmostEqual(result['predicted_starts'], 10, delta=1)

    def test_explanations_match_the_numbers(self):
        order = self._order('On bench', 'ON_BENCH', order_day=50)
        self._history(order, None, 'NEW', self.first_run, observed=False)
        self._history(order, 'NEW', 'ON_BENCH', self.now - 5 * DAY)

        _, estimates = self._estimates()

        self.assertEqual(
            estimates['Waiting 1'].explanation,
            "Your order is #2 in the build queue. Decware has been starting about 2 orders a week, "
            "and a build takes about 14 days. This estimate will firm up as more recent progress is recorded.",
        )
        self.assertEqual(
            estimates['On bench'].explanation,
            "Your order is being built (on bench). Builds usually take about 14 days "
            "from start to passing quality control.",
        )

    def test_overdue_build_says_so(self):
        order = self._order('Slow', 'TESTING', order_day=50)
        self._history(order, None, 'NEW', self.first_run, observed=False)
        self._history(order, 'NEW', 'ON_BENCH', self.now - 30 * DAY)
        self._history(order, 'ON_BENCH', 'TESTING', self.now - 10 * DAY)

        _, estimates = self._estimates()

        self.assertIn("taking longer than the typical 14 days", estimates['Slow'].explanation)
