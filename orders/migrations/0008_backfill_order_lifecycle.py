"""
Backfills the lifecycle fields added in 0007 from existing data.

Past scraper runs aren't recorded anywhere, so they're reconstructed from the
timestamps they left behind: every run saved each order in the CSV (bumping
time_updated) and wrote StatusHistory rows for changes it saw.
"""
import bisect
import datetime

from django.db import migrations

# Keep in sync with orders.scraper.MAX_OBSERVED_RUN_GAP
MAX_OBSERVED_RUN_GAP = datetime.timedelta(days=3)


def backfill(apps, schema_editor):
    OrderRecord = apps.get_model('orders', 'OrderRecord')
    StatusHistory = apps.get_model('orders', 'StatusHistory')

    # One representative timestamp per day a run happened (the latest write that day)
    run_by_day = {}
    for ts in list(OrderRecord.objects.values_list('time_updated', flat=True)) + \
            list(StatusHistory.objects.values_list('timestamp', flat=True)):
        day = ts.date()
        if day not in run_by_day or ts > run_by_day[day]:
            run_by_day[day] = ts
    runs = sorted(run_by_day.values())
    if not runs:
        return
    run_days = [run.date() for run in runs]
    latest_run_day = run_days[-1]

    # Orders last saved before the latest run dropped off the list. They were removed
    # by the first run after they were last seen; removed_at - last_seen_at shows how
    # precisely we know that.
    orders = list(OrderRecord.objects.all())
    for order in orders:
        order.last_seen_at = order.time_updated
        if order.time_updated.date() < latest_run_day:
            next_run = bisect.bisect_right(run_days, order.time_updated.date())
            order.removed_at = runs[next_run]
    OrderRecord.objects.bulk_update(orders, ['last_seen_at', 'removed_at'], batch_size=500)

    # First rows don't mark when the status began
    StatusHistory.objects.filter(previous_status__isnull=True).update(is_observed=False)

    # Changes spotted on the first run after a gap could have happened anytime in the gap
    unobserved_ids = []
    for row in StatusHistory.objects.filter(previous_status__isnull=False).only('id', 'timestamp'):
        prev = bisect.bisect_left(runs, row.timestamp) - 1
        if prev < 0 or row.timestamp - runs[prev] > MAX_OBSERVED_RUN_GAP:
            unobserved_ids.append(row.id)
    StatusHistory.objects.filter(id__in=unobserved_ids).update(is_observed=False)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_order_lifecycle_tracking'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
