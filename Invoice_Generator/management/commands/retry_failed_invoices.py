"""FEATURE 11: recovery for MISSING invoices only.

  python manage.py retry_failed_invoices

Finds successful payments with no invoice (generation crashed) -> creates Draft.
Idempotent. Safe twice, safe in parallel.
Emails are NOT retried here: staff controls sending from dashboard.
"""
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from billing.services.adapters import PAID_STATUS
from billing.pipeline import process_paid_payment


class Command(BaseCommand):
    help = "Create Draft invoices for paid payments that have none."

    def handle(self, *args, **opts):
        Payment = apps.get_model(settings.BILLING_PAYMENT_MODEL)
        ids = list(
            Payment.objects.filter(status=PAID_STATUS, invoice__isnull=True)
            .values_list("pk", flat=True)
        )
        for pid in ids:
            process_paid_payment(pid)
        self.stdout.write(self.style.SUCCESS(f"Processed {len(ids)} payments without invoice"))
