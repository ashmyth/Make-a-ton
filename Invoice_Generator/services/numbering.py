"""Feature 1 & PRD 7.9: Contiguous, gap-safe sequential invoice numbers (e.g., INV-2026-00001).
Uses InvoiceSequence with select_for_update inside an atomic transaction.
"""
from django.db import transaction
from django.utils import timezone

from billing.models import InvoiceSequence


def next_invoice_number() -> str:
    """Generate next sequential invoice number for current year with pessimistic lock."""
    year = timezone.localdate().year
    with transaction.atomic():
        seq, _ = InvoiceSequence.objects.select_for_update().get_or_create(
            year=year,
            defaults={"last_number": 0}
        )
        seq.last_number += 1
        seq.save(update_fields=["last_number"])
        return f"INV-{year}-{seq.last_number:05d}"

