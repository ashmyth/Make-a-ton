from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.subscriptions.models import Subscription, SubscriptionStatus
from apps.billing.models import Invoice, InvoiceStatus
from apps.payments.models import Payment, PaymentStatus


def calculate_dashboard_metrics(
    *,
    start_date=None,
    end_date=None,
    customer_id=None,
    plan_name=None,
):
    """
    Computes the 7 PRD §7.13 financial and subscription metrics strictly from database records.
    Filters:
      - start_date / end_date: applied to invoice issue_date for billed amount,
        and payment paid_at for cash collected.
      - customer_id: filter by a specific customer.
      - plan_name: filter subscriptions and invoices by plan.
    """
    today = timezone.now().date()

    # 1 & 2: Subscriptions (Active & Running)
    subs_qs = Subscription.objects.all()
    if customer_id:
        subs_qs = subs_qs.filter(customer_id=customer_id)
    if plan_name:
        subs_qs = subs_qs.filter(plan_name=plan_name)

    active_subscriptions = subs_qs.filter(status=SubscriptionStatus.ACTIVE).count()
    running_subscriptions = subs_qs.filter(status=SubscriptionStatus.ACTIVE, is_paused=False).count()

    # 3: Billed Amount
    # Confirmed, partially paid, and paid invoice totals issued in the selected period (excluding cancelled & draft)
    invoices_qs = Invoice.objects.filter(
        status__in=[InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID]
    )
    if customer_id:
        invoices_qs = invoices_qs.filter(customer_id=customer_id)
    if plan_name:
        invoices_qs = invoices_qs.filter(subscription__plan_name=plan_name)
    if start_date:
        invoices_qs = invoices_qs.filter(issue_date__gte=start_date)
    if end_date:
        invoices_qs = invoices_qs.filter(issue_date__lte=end_date)

    billed_amount_agg = invoices_qs.aggregate(total=Sum("total"))["total"] or Decimal("0.00")

    # 4: Cash Collected
    # Recorded succeeded payments in the selected period, net of reversals
    payments_qs = Payment.objects.filter(is_reversed=False, status=PaymentStatus.SUCCEEDED)
    if customer_id:
        payments_qs = payments_qs.filter(customer_id=customer_id)
    if plan_name:
        payments_qs = payments_qs.filter(invoice__subscription__plan_name=plan_name)
    if start_date:
        payments_qs = payments_qs.filter(paid_at__date__gte=start_date)
    if end_date:
        payments_qs = payments_qs.filter(paid_at__date__lte=end_date)

    cash_collected_agg = payments_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # 5: Outstanding Balance
    # Unpaid balance across non-cancelled, confirmed and partially paid invoices
    unpaid_invoices_qs = Invoice.objects.filter(
        status__in=[InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID]
    )
    if customer_id:
        unpaid_invoices_qs = unpaid_invoices_qs.filter(customer_id=customer_id)
    if plan_name:
        unpaid_invoices_qs = unpaid_invoices_qs.filter(subscription__plan_name=plan_name)

    outstanding_balance_agg = unpaid_invoices_qs.aggregate(total=Sum("outstanding_balance"))["total"] or Decimal("0.00")

    # 6 & 7: Overdue Balance & Overdue Invoice Count
    # Invoices where due_date < today
    overdue_invoices_qs = unpaid_invoices_qs.filter(due_date__lt=today)
    overdue_balance_agg = overdue_invoices_qs.aggregate(total=Sum("outstanding_balance"))["total"] or Decimal("0.00")
    overdue_invoice_count = overdue_invoices_qs.count()

    return {
        "active_subscriptions": active_subscriptions,
        "running_subscriptions": running_subscriptions,
        "billed_amount": billed_amount_agg,
        "cash_collected": cash_collected_agg,
        "outstanding_balance": outstanding_balance_agg,
        "overdue_balance": overdue_balance_agg,
        "overdue_invoice_count": overdue_invoice_count,
        "currency": "INR",
        "filter_summary": {
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "customer_id": str(customer_id) if customer_id else None,
            "plan_name": plan_name,
            "evaluated_at": str(today),
        }
    }


def build_invoices_workbook(invoices_qs):
    """
    Builds an openpyxl Workbook from a queryset of Invoices.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices Register"

    columns = [
        ("Invoice Number", "invoice_number"),
        ("Issue Date", "issue_date"),
        ("Due Date", "due_date"),
        ("Customer", "customer_name"),
        ("Email", "customer_email"),
        ("Status", "status"),
        ("Subtotal", "subtotal"),
        ("Tax Total", "tax_total"),
        ("Discount Total", "discount_total"),
        ("Grand Total", "total"),
        ("Paid Amount", "amount_paid"),
        ("Outstanding Balance", "outstanding_balance"),
    ]

    header_fill = PatternFill("solid", fgColor="1F4E78")
    ws.append([col[0] for col in columns])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
    ws.freeze_panes = "A2"

    for inv in invoices_qs:
        row = [
            inv.invoice_number,
            str(inv.issue_date) if inv.issue_date else "",
            str(inv.due_date) if inv.due_date else "",
            inv.customer_name,
            inv.customer_email,
            inv.status,
            float(inv.subtotal),
            float(inv.tax_total),
            float(inv.discount_total),
            float(inv.total),
            float(inv.amount_paid),
            float(inv.outstanding_balance),
        ]
        ws.append(row)

    for i, (title, _) in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(14, len(title) + 4)
    ws.auto_filter.ref = ws.dimensions
    return wb


def build_payments_workbook(payments_qs):
    """
    Builds an openpyxl Workbook from a queryset of Payments.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Payments Register"

    columns = [
        ("Payment ID", "id"),
        ("Payment Date", "paid_at"),
        ("Invoice Number", "invoice_number"),
        ("Customer", "customer_name"),
        ("Method", "method"),
        ("Amount", "amount"),
        ("Currency", "currency"),
        ("Status", "status"),
        ("Reversed", "is_reversed"),
        ("External Reference", "external_reference"),
        ("Note", "note"),
    ]

    header_fill = PatternFill("solid", fgColor="1F4E78")
    ws.append([col[0] for col in columns])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
    ws.freeze_panes = "A2"

    for pay in payments_qs:
        inv_no = pay.invoice.invoice_number if pay.invoice else ""
        cust_name = getattr(pay.customer, "display_name", "") if pay.customer else ""
        paid_at_str = pay.paid_at.strftime("%Y-%m-%d %H:%M:%S") if pay.paid_at else ""
        row = [
            str(pay.id),
            paid_at_str,
            inv_no,
            cust_name,
            pay.method,
            float(pay.amount),
            pay.currency,
            pay.status,
            "Yes" if pay.is_reversed else "No",
            pay.external_reference or "",
            getattr(pay, "notes", "") or getattr(pay, "note", "") or "",
        ]
        ws.append(row)

    for i, (title, _) in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(14, len(title) + 4)
    ws.auto_filter.ref = ws.dimensions
    return wb

