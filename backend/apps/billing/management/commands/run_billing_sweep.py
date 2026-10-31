from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.billing.services.recurring import run_billing_sweep


class Command(BaseCommand):
    help = "Execute the recurring billing sweep across active subscriptions (BILL-01..08)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--as-of",
            type=str,
            help="Evaluate billing due as of YYYY-MM-DD (defaults to today)",
        )

    def handle(self, *args, **options):
        as_of_str = options.get("as_of")
        if as_of_str:
            as_of = datetime.strptime(as_of_str, "%Y-%m-%d").date()
        else:
            as_of = timezone.localdate()

        self.stdout.write(f"Running recurring billing sweep as of {as_of}...")
        results = run_billing_sweep(as_of=as_of)

        gen_count = len(results["generated"])
        fail_count = len(results["failed"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Billing sweep complete: {gen_count} invoices generated, {fail_count} failures recorded."
            )
        )
        for inv in results["generated"]:
            self.stdout.write(f"  + Generated {inv.invoice_number} ({inv.currency} {inv.total}) for Sub {inv.subscription_number}")

        for sub_id, err in results["failed"]:
            self.stdout.write(self.style.ERROR(f"  ! Error on Sub {sub_id}: {err}"))

