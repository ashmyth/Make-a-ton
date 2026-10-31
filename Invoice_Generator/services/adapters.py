"""Adapters to decouple Billing from Teammate 1 (Identity), 2 (Subscription), and 4 (Payment).
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional

from .calculation import InputLine

PAID_STATUS = "paid"


@dataclass
class InvoiceInput:
    customer_id: any
    customer_name: str
    customer_email: str
    billing_address: str
    subscription_id: str
    subscription_number: str
    period_start: Optional[date]
    period_end: Optional[date]
    currency: str
    payment_terms_days: int
    lines: List[InputLine] = field(default_factory=list)
    discount: Optional[dict] = None


def is_payment_successful(payment) -> bool:
    """Check if payment is marked as successful/paid."""
    status = getattr(payment, "status", None)
    if isinstance(status, str):
        return status.lower() in ("paid", "succeeded", "success", "completed")
    return bool(getattr(payment, "is_successful", False))


def build_invoice_input(payment) -> InvoiceInput:
    """Extract standard billing input from a Payment instance and its linked relations."""
    # Determine customer details
    user = getattr(payment, "user", None) or getattr(payment, "customer", None)
    customer_id = getattr(user, "pk", getattr(payment, "customer_id", None))

    first_name = getattr(user, "first_name", "")
    last_name = getattr(user, "last_name", "")
    full_name = f"{first_name} {last_name}".strip() or getattr(user, "username", "Valued Customer")
    customer_name = getattr(payment, "customer_name", full_name)
    customer_email = getattr(payment, "customer_email", getattr(user, "email", "billing@customer.com"))
    billing_address = getattr(payment, "billing_address", getattr(user, "address", ""))

    # Determine subscription details
    sub = getattr(payment, "subscription", None)
    sub_id = str(getattr(sub, "pk", getattr(payment, "subscription_id", "")))
    sub_number = str(getattr(sub, "subscription_number", getattr(payment, "subscription_number", sub_id)))
    period_start = getattr(payment, "period_start", getattr(sub, "period_start", None))
    period_end = getattr(payment, "period_end", getattr(sub, "period_end", None))
    currency = getattr(payment, "currency", getattr(sub, "currency", "INR"))
    payment_terms_days = getattr(sub, "payment_terms_days", 14)

    # Determine line items
    lines: List[InputLine] = []
    sub_lines = getattr(sub, "lines", None) or getattr(payment, "lines", None)

    if sub_lines is not None:
        raw_items = sub_lines.all() if hasattr(sub_lines, "all") else sub_lines
        for item in raw_items:
            lines.append(
                InputLine(
                    description=getattr(item, "description", getattr(getattr(item, "product", None), "name", "Subscription Service")),
                    quantity=Decimal(str(getattr(item, "quantity", 1))),
                    unit_price=Decimal(str(getattr(item, "unit_price", 0))),
                    discount_amount=Decimal(str(getattr(item, "discount_amount", 0))),
                    tax_rate=Decimal(str(getattr(item, "tax_rate", 0))),
                )
            )

    # Fallback to single payment line if no subscription line items are defined
    if not lines:
        amount = Decimal(str(getattr(payment, "amount", 0)))
        lines.append(
            InputLine(
                description=getattr(payment, "description", f"Subscription Payment ({sub_number or 'Plan'})"),
                quantity=Decimal("1"),
                unit_price=amount,
                discount_amount=Decimal("0.00"),
                tax_rate=Decimal("0.00"),
            )
        )

    # Subscription-level or payment-level discount if present
    discount = getattr(payment, "discount", getattr(sub, "discount", None))

    return InvoiceInput(
        customer_id=customer_id,
        customer_name=customer_name,
        customer_email=customer_email,
        billing_address=billing_address,
        subscription_id=sub_id,
        subscription_number=sub_number,
        period_start=period_start,
        period_end=period_end,
        currency=currency,
        payment_terms_days=payment_terms_days,
        lines=lines,
        discount=discount,
    )

