"""
Django management command to recompute estimated Passed QC dates for active orders.
"""
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from orders.estimation import backtest, compute_estimates


class Command(BaseCommand):
    help = 'Recomputes estimated completion dates, or backtests the estimates with --backtest DATE'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backtest', metavar='YYYY-MM-DD',
            help='Estimate as of this date using only data known then, and compare with what happened since',
        )

    def handle(self, *args, **options):
        if options['backtest']:
            as_of = timezone.make_aware(datetime.datetime.fromisoformat(options['backtest']))
            result = backtest(as_of)
            if result is None:
                raise CommandError(f"No data as of {options['backtest']}")
            for key, value in result.items():
                self.stdout.write(f"{key}: {round(value, 2) if isinstance(value, float) else value}")
            return

        model, count = compute_estimates()
        if model is None:
            raise CommandError("No order data to estimate from")
        self.stdout.write(self.style.SUCCESS(
            f"Stored {count} estimates. Starts/week: {model.starts_per_week:.1f} "
            f"({model.precise_starts} precisely timed), build days: {model.build_typical_days:.1f} typical / "
            f"{model.build_late_days:.1f} late from {model.build_samples} builds"
        ))
