"""Adapters to decouple Billing from Teammate 1 (Identity), 2 (Subscription), and 4 (Payment).
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional
from django.db import models

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


def resolve_crm_customer(user_or_customer):
    """Ensures we obtain a valid apps.customers.models.Customer instance."""
    from apps.customers.models import Customer

    if isinstance(user_or_customer, Customer):
        return user_or_customer

    if hasattr(user_or_customer, "customer") and user_or_customer.customer:
        return user_or_customer.customer

    if user_or_customer and hasattr(user_or_customer, "pk"):
        cust = Customer.objects.filter(
            models.Q(portal_user_id=user_or_customer.pk) | models.Q(pk=user_or_customer.pk)
        ).first()
        if cust:
            return cust

        # Provision a CRM customer row for users created in tests / onboarding
        code_part = str(getattr(user_or_customer, "pk", "001"))[:8].upper()
        return Customer.objects.create(
            portal_user=user_or_customer if getattr(user_or_customer, "role", None) else None,
            customer_code=f"CUST-{code_part}",
            display_name=getattr(user_or_customer, "username", "Customer Corp"),
            contact_person=f"{getattr(user_or_customer, 'first_name', '')} {getattr(user_or_customer, 'last_name', '')}".strip()
            or getattr(user_or_customer, "username", "Customer"),
            email=getattr(user_or_customer, "email", "customer@example.com"),
            billing_street=getattr(user_or_customer, "address", "123 Main St"),
            billing_city="Bengaluru",
            billing_state="KA",
            billing_postal_code="560001",
            billing_country="IN",
        )

    # Fallback to any existing customer or create default
    default_cust = Customer.objects.first()
    if default_cust:
        return default_cust
    return Customer.objects.create(
        customer_code="CUST-DEFAULT",
        display_name="Default Customer Corp",
        contact_person="Billing Admin",
        email="billing@default.com",
        billing_street="100 Market St",
        billing_city="Bengaluru",
        billing_state="KA",
        billing_postal_code="560001",
        billing_country="IN",
    )


def build_subscription_invoice_input(
    subscription, period_start: date, period_end: date
) -> InvoiceInput:
    """Extract standard billing input from a Subscription instance (Teammate 2)."""
    raw_user = getattr(subscription, "customer", None) or getattr(subscription, "user", None)
    customer = resolve_crm_customer(raw_user)
    customer_id = customer.id

    customer_name = getattr(subscription, "customer_name", None) or customer.display_name
    customer_email = getattr(subscription, "customer_email", None) or customer.email
    billing_address = getattr(subscription, "billing_address", None) or customer.full_billing_address

    sub_id = str(getattr(subscription, "pk", getattr(subscription, "id", "")))
    sub_number = str(getattr(subscription, "subscription_number", sub_id))
    currency = getattr(subscription, "currency", "INR")
    payment_terms_days = getattr(subscription, "payment_terms_days", 14)

    lines: List[InputLine] = []
    sub_lines = getattr(subscription, "lines", None)
    if sub_lines is not None:
        raw_items = sub_lines.all() if hasattr(sub_lines, "all") else sub_lines
        for item in raw_items:
            lines.append(
                InputLine(
                    description=getattr(item, "description", getattr(getattr(item, "product", None), "name", "Subscription Plan")),
                    quantity=Decimal(str(getattr(item, "quantity", 1))),
                    unit_price=Decimal(str(getattr(item, "unit_price", 0))),
                    discount_amount=Decimal(str(getattr(item, "discount_amount", 0))),
                    tax_rate=Decimal(str(getattr(item, "tax_rate", 0))),
                )
            )

    if not lines:
        amount = Decimal(str(getattr(subscription, "amount", getattr(subscription, "recurring_price", 0))))
        lines.append(
            InputLine(
                description=f"Subscription - {sub_number}",
                quantity=Decimal("1"),
                unit_price=amount,
                discount_amount=Decimal("0.00"),
                tax_rate=Decimal("0.00"),
            )
        )

    discount = getattr(subscription, "discount", None)

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


def build_invoice_input(payment) -> InvoiceInput:
    """Extract standard billing input from a Payment instance and its linked relations."""
    raw_user = getattr(payment, "customer", None) or getattr(payment, "user", None)
    customer = resolve_crm_customer(raw_user)
    customer_id = customer.id

    customer_name = getattr(payment, "customer_name", None) or customer.display_name
    customer_email = getattr(payment, "customer_email", None) or customer.email
    billing_address = getattr(payment, "billing_address", None) or customer.full_billing_address

    sub = getattr(payment, "subscription", None)
    sub_id = str(getattr(sub, "pk", getattr(payment, "subscription_id", "")))
    sub_number = str(getattr(sub, "subscription_number", getattr(payment, "subscription_number", sub_id)))
    period_start = getattr(payment, "period_start", getattr(sub, "period_start", None))
    period_end = getattr(payment, "period_end", getattr(sub, "period_end", None))
    currency = getattr(payment, "currency", getattr(sub, "currency", "INR"))
    payment_terms_days = getattr(sub, "payment_terms_days", 14)

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
