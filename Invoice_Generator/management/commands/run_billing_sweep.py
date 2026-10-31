"""Management command to trigger a recurring billing sweep.

Usage:
  python manage.py run_billing_sweep
  python manage.py run_billing_sweep --as-of 2026-11-01
"""
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from billing.services.recurring import run_billing_sweep


class Command(BaseCommand):
    help = "Run the recurring billing sweep to generate invoices for due subscriptions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--as-of",
            type=str,
            help="Simulate the sweep as of a specific date (YYYY-MM-DD)",
            default=None,
        )

    def handle(self, *args, **options):
        as_of = None
        if options.get("as_of"):
            as_of = datetime.strptime(options["as_of"], "%Y-%m-%d").date()
        else:
            as_of = timezone.localdate()

        self.stdout.write(f"Starting recurring billing sweep as of {as_of}...")
        results = run_billing_sweep(as_of=as_of)

        self.stdout.write(
            self.style.SUCCESS(
                f"Billing sweep completed: {len(results['generated'])} invoices generated, "
                f"{len(results['failed'])} failures recorded."
            )
        )
