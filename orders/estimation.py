"""
Estimates when active orders will pass QC.

Decware builds orders first come, first served, and nearly all of the wait is
spent in NEW: orders wait years to start and are built in about two weeks. So
an order's estimate is the time until every order ahead of it has started
(queue position / start rate), plus the build time still remaining.

Past scraper runs missed long stretches, so many events are only known to have
happened sometime between two runs. Those are spread evenly over that interval.
"""
import bisect
import datetime
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import OrderRecord, StatusHistory, OrderEstimate

DONE_STATUSES = {'PASSED_QC', 'PASSED_QC_AWAITING_PAYMENT', 'COMPLETED_WAITING_BASE'}
# The start rate is measured over this much recent history (or all of it, if less)
RATE_WINDOW = datetime.timedelta(weeks=52)
# The late end of the range assumes orders start this much slower than the measured rate.
# A few weeks' rate can run ~50% fast: May 2025 measured 15.5/week, the next 17 months
# averaged 10.2/week.
SLOW_RATE_FACTOR = 0.65
# Build days (typical, late) used until enough builds have been observed
DEFAULT_BUILD_DAYS = (14.0, 21.0)
MIN_BUILD_SAMPLES = 5
# Events known to within this long count as precisely timed
PRECISE_GAP = datetime.timedelta(days=3)
# Orders that drop off while NEW count as started only if fewer than this many orders
# were still waiting ahead of them (the shop builds roughly, not strictly, in order)
OUT_OF_ORDER_ALLOWANCE = 50
# Timestamps closer together than this were written by the same scraper run
RUN_GROUPING = datetime.timedelta(hours=1)

DAY = datetime.timedelta(days=1)
WEEK = datetime.timedelta(weeks=1)


@dataclass
class Model:
    starts_per_week: float
    precise_starts: int  # Starts in the rate window that were timed to within PRECISE_GAP
    build_typical_days: float
    build_late_days: float
    build_samples: int


def _percentile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    low = int(pos)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (pos - low)


def _load(as_of):
    """Orders and their history, as far as they were known at `as_of`."""
    orders = list(OrderRecord.objects.filter(time_created__lte=as_of))
    history = {}
    for row in StatusHistory.objects.filter(timestamp__lte=as_of).order_by('timestamp'):
        history.setdefault(row.order_id, []).append(row)
    return orders, history


def _run_times(orders, history, as_of):
    """End times of past scraper runs, reconstructed from the timestamps they wrote."""
    times = {row.timestamp for rows in history.values() for row in rows}
    for order in orders:
        times.update(t for t in (order.last_seen_at, order.removed_at) if t and t <= as_of)
    # One run writes many timestamps a little apart; keep the last one of each run
    runs = []
    for t in sorted(times):
        if runs and t - runs[-1] < RUN_GROUPING:
            runs[-1] = t
        else:
            runs.append(t)
    return runs


def _left_new(order, rows, runs, as_of):
    """(earliest, latest) time the order left NEW, or None if it hadn't by `as_of`."""
    row = next((r for r in rows if r.previous_status == 'NEW'), None)
    if row and row.is_observed:
        return row.timestamp, row.timestamp
    if row:
        # Seen after missed runs: it left NEW sometime after the run before
        prev = bisect.bisect_left(runs, row.timestamp) - 1
        return (runs[prev] if prev >= 0 else row.timestamp), row.timestamp
    if order.removed_at and order.removed_at <= as_of and order.status == 'NEW':
        return order.last_seen_at, order.removed_at
    return None


def _starts(orders, history, runs, as_of):
    """
    {order pk: (earliest, latest) time it was started}. Orders that dropped off the list while
    still NEW only count if they were near the front of the queue; ones further back were
    cancelled or edited (edits re-key the order), which doesn't move the queue forward.
    """
    left = {}
    for order in orders:
        rows = history.get(order.pk, [])
        interval = _left_new(order, rows, runs, as_of)
        if interval:
            left[order.pk] = interval
    # When each order stopped waiting (orders still waiting never did)
    waiting_until = {pk: interval[1] for pk, interval in left.items()}
    for order in orders:
        rows = history.get(order.pk, [])
        if order.pk not in left and (rows[-1].new_status if rows else order.status) == 'NEW':
            waiting_until[order.pk] = datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)

    by_pk = {o.pk: o for o in orders}
    starts = {}
    dropped = {}
    for pk, interval in left.items():
        if any(r.previous_status == 'NEW' for r in history.get(pk, [])):
            starts[pk] = interval  # Moved into a build status
        else:
            dropped.setdefault(interval[1], []).append(pk)
    for removed_at, pks in dropped.items():
        still_waiting = sorted(by_pk[pk].order_date for pk, until in waiting_until.items() if until > removed_at)
        for pk in pks:
            if bisect.bisect_left(still_waiting, by_pk[pk].order_date) < OUT_OF_ORDER_ALLOWANCE:
                starts[pk] = left[pk]
    return starts


def _start_rate(starts, runs, as_of):
    """Orders leaving NEW per week over the rate window, and how many were precisely timed."""
    window_start = max(as_of - RATE_WINDOW, runs[0])
    weeks = (as_of - window_start) / WEEK
    if weeks <= 0:
        return 0.0, 0
    total, precise = 0.0, 0
    for earliest, latest in starts:
        if latest <= window_start or earliest >= as_of:
            continue
        span = latest - earliest
        if span <= PRECISE_GAP:
            total += 1
            precise += 1
        else:
            total += (min(latest, as_of) - max(earliest, window_start)) / span
    return total / weeks, precise


def _build_days(orders, history, as_of):
    """Observed days from leaving NEW to passing QC, as known at `as_of`."""
    samples = []
    for order in orders:
        rows = history.get(order.pk, [])
        start = next((r for r in rows if r.previous_status == 'NEW' and r.is_observed), None)
        if not start:
            continue
        done = next((r for r in rows if r.new_status in DONE_STATUSES and r.is_observed
                     and r.timestamp > start.timestamp), None)
        if done:
            end = done.timestamp
        elif (order.removed_at and order.removed_at <= as_of and order.status == 'QUALITY_CONTROL'
              and order.removed_at - order.last_seen_at <= PRECISE_GAP):
            # Orders now drop off the list right after QC, so leaving from QC counts as passing
            end = order.removed_at
        else:
            continue
        samples.append((end - start.timestamp) / DAY)
    return samples


def build_model(as_of):
    orders, history = _load(as_of)
    runs = _run_times(orders, history, as_of)
    if not runs:
        return None, orders, history, runs
    starts = _starts(orders, history, runs, as_of)
    rate, precise = _start_rate(starts.values(), runs, as_of)
    builds = _build_days(orders, history, as_of)
    if len(builds) >= MIN_BUILD_SAMPLES:
        typical, late = _percentile(builds, 0.5), _percentile(builds, 0.8)
    else:
        typical, late = DEFAULT_BUILD_DAYS
    return Model(rate, precise, typical, late, len(builds)), orders, history, runs


def _confidence(model, waiting, days_out=0):
    if model.build_samples < MIN_BUILD_SAMPLES:
        return 'LOW'
    if not waiting:
        return 'HIGH' if model.build_samples >= 20 else 'MEDIUM'
    if model.precise_starts < 15:
        return 'LOW'
    if model.precise_starts < 40 or days_out > 365:
        return 'MEDIUM'
    return 'HIGH'


def estimate_orders(as_of=None):
    """Returns (model, [OrderEstimate]) for orders active at `as_of` (unsaved)."""
    as_of = as_of or timezone.now()
    model, orders, history, runs = build_model(as_of)
    if model is None:
        return None, []

    def active(order):
        rows = history.get(order.pk, [])
        status = rows[-1].new_status if rows else order.status
        removed = order.removed_at and order.removed_at <= as_of
        return not removed and status not in DONE_STATUSES, status

    estimates = []
    queue = []
    for order in orders:
        is_active, status = active(order)
        if not is_active:
            continue
        if status == 'NEW':
            queue.append(order)
            continue
        # Being built: what's left of the build time
        rows = history.get(order.pk, [])
        left_new = _left_new(order, rows, runs, as_of)
        started = left_new[1] if left_new else (rows[0].timestamp if rows else order.time_created)
        elapsed = (as_of - started) / DAY
        typical = max(1.0, model.build_typical_days - elapsed)
        late = max(typical, model.build_late_days - elapsed)
        confidence = _confidence(model, waiting=False)
        estimates.append(_estimate(order, as_of, typical, late, None, confidence,
                                   _building_explanation(status, model, elapsed)))

    if model.starts_per_week > 0:
        queue.sort(key=lambda o: (o.order_date, o.pk))
        for position, order in enumerate(queue):
            weeks = (position + 1) / model.starts_per_week
            typical = weeks * 7 + model.build_typical_days
            late = weeks / SLOW_RATE_FACTOR * 7 + model.build_late_days
            confidence = _confidence(model, waiting=True, days_out=typical)
            estimates.append(_estimate(order, as_of, typical, late, position, confidence,
                                       _waiting_explanation(position, model, confidence)))
    return model, estimates


def _waiting_explanation(position, model, confidence):
    text = (
        f"Your order is #{position + 1:,} in the build queue. Decware has been starting about "
        f"{model.starts_per_week:.0f} orders a week, and a build takes about {model.build_typical_days:.0f} days."
    )
    if confidence == 'LOW':
        text += " This estimate will firm up as more recent progress is recorded."
    return text


def _building_explanation(status, model, elapsed_days):
    label = dict(OrderRecord.STATUS_CHOICES).get(status, status).lower()
    if elapsed_days > model.build_late_days:
        return (f"Your order is being built ({label}) and is taking longer than the typical "
                f"{model.build_typical_days:.0f} days.")
    return (f"Your order is being built ({label}). Builds usually take about "
            f"{model.build_typical_days:.0f} days from start to passing quality control.")


def _estimate(order, as_of, typical_days, late_days, position, confidence, explanation):
    return OrderEstimate(
        order=order,
        estimated_date=(as_of + typical_days * DAY).date(),
        range_end_date=(as_of + late_days * DAY).date(),
        queue_position=position,
        confidence_level=confidence,
        explanation=explanation,
        computed_at=as_of,
    )


def compute_estimates():
    """Replaces all stored estimates with fresh ones. Returns (model, count)."""
    model, estimates = estimate_orders()
    with transaction.atomic():
        OrderEstimate.objects.all().delete()
        OrderEstimate.objects.bulk_create(estimates, batch_size=500)
    return model, len(estimates)


def backtest(as_of, now=None):
    """
    Estimates start dates for the orders waiting at `as_of` using only what was known
    then, and compares them with when those orders actually left NEW.
    """
    now = now or timezone.now()
    model, estimates = estimate_orders(as_of)
    if model is None:
        return None
    orders_now, history_now = _load(now)
    starts_now = _starts(orders_now, history_now, _run_times(orders_now, history_now, now), now)

    errors, in_range, started, precise = [], 0, 0, 0
    for est in estimates:
        actual = starts_now.get(est.order_id)
        if est.queue_position is None or not actual:
            continue
        started += 1
        precise += actual[1] - actual[0] <= PRECISE_GAP
        # Compare predicted start dates (estimate minus build time) with the actual start window
        typical_start = est.estimated_date - datetime.timedelta(days=model.build_typical_days)
        late_start = est.range_end_date - datetime.timedelta(days=model.build_late_days)
        earliest, latest = actual[0].date(), actual[1].date()
        if typical_start < earliest:
            errors.append((earliest - typical_start).days)
        elif typical_start > latest:
            errors.append((typical_start - latest).days)
        else:
            errors.append(0)
        if typical_start <= latest and late_start >= earliest:
            in_range += 1

    weeks = (now - as_of) / WEEK
    return {
        'starts_per_week': model.starts_per_week,
        'predicted_starts': model.starts_per_week * weeks,
        'actual_starts': started,
        'precisely_timed_actual_starts': precise,
        'waiting_at_as_of': sum(1 for e in estimates if e.queue_position is not None),
        'median_error_days': _percentile(errors, 0.5) if errors else None,
        'in_range_share': in_range / started if started else None,
    }
