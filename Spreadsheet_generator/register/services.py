"""Sync DB -> RegisterEntry rows -> XLSX workbook."""
import os
import tempfile

from django.conf import settings
from django.db import transaction
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from sales.models import Order

from .models import RegisterEntry


def sync_order(order_id: int) -> None:
    """Idempotent: rebuild all register rows for one order."""
    try:
        order = (Order.objects.select_related("customer", "plan")
                 .get(pk=order_id))
    except Order.DoesNotExist:
        RegisterEntry.objects.filter(order_id_ref=order_id).delete()
        return

    # Drafts are not purchases yet.
    if order.status == Order.Status.DRAFT:
        RegisterEntry.objects.filter(order_id_ref=order.pk).delete()
        return

    total, paid = order.total, order.paid
    pay_status = order.payment_status
    lines = list(order.lines.select_related("product", "variant"))

    with transaction.atomic():
        keep = []
        for ln in lines:
            RegisterEntry.objects.update_or_create(
                order_line=ln,
                defaults=dict(
                    order_id_ref=order.pk,
                    order_number=order.number or "",
                    purchase_date=order.confirmed_at or order.created_at,
                    order_status=order.status,
                    kind=order.kind,
                    customer_name=order.customer.name,
                    customer_email=order.customer.email,
                    customer_phone=order.customer.phone,
                    product=ln.product.name,
                    variant=(f"{ln.variant.attribute}: {ln.variant.value}" if ln.variant else ""),
                    quantity=ln.quantity,
                    unit_price=ln.unit_price,
                    line_total=ln.line_total,
                    plan=order.plan.name if order.plan else "",
                    billing_interval=order.plan.interval if order.plan else "",
                    start_date=order.start_date,
                    expiry_date=order.expiry_date,
                    order_total=total,
                    amount_paid=paid,
                    balance=total - paid,
                    payment_status=pay_status,
                ),
            )
            keep.append(ln.pk)
        RegisterEntry.objects.filter(order_id_ref=order.pk).exclude(order_line_id__in=keep).delete()


# ---------------------------------------------------------------- workbook
COLUMNS = [
    ("Order No", "order_number"), ("Purchase Date", "purchase_date"),
    ("Status", "order_status"), ("Type", "kind"),
    ("Customer", "customer_name"), ("Email", "customer_email"), ("Phone", "customer_phone"),
    ("Product", "product"), ("Variant", "variant"),
    ("Qty", "quantity"), ("Unit Price", "unit_price"), ("Line Total", "line_total"),
    ("Plan", "plan"), ("Interval", "billing_interval"),
    ("Start", "start_date"), ("Expiry", "expiry_date"),
    ("Order Total", "order_total"), ("Paid", "amount_paid"),
    ("Balance", "balance"), ("Payment Status", "payment_status"),
]
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")


def _write_sheet(ws, qs):
    ws.append([c[0] for c in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
    ws.freeze_panes = "A2"
    for e in qs.iterator():
        row = []
        for _, attr in COLUMNS:
            v = getattr(e, attr)
            if attr == "purchase_date" and v is not None:
                v = v.astimezone().replace(tzinfo=None)    # xlsx has no tz
            elif hasattr(v, "quantize"):                    # Decimal
                v = float(v)
            row.append(v)
        ws.append(row)
    for i, (title, _) in enumerate(COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(12, len(title) + 4)
    ws.auto_filter.ref = ws.dimensions


def build_workbook() -> Workbook:
    qs = RegisterEntry.objects.all()
    wb = Workbook()
    ws = wb.active
    ws.title = "All Purchases"
    _write_sheet(ws, qs)
    _write_sheet(wb.create_sheet("Subscriptions"), qs.filter(kind="subscription"))
    _write_sheet(wb.create_sheet("Products"), qs.filter(kind="product"))
    return wb


def export_workbook() -> str:
    """Write workbook atomically (temp file + rename) so readers never see half a file."""
    path = str(settings.REGISTER_XLSX_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".xlsx", dir=os.path.dirname(path))
    os.close(fd)
    try:
        build_workbook().save(tmp)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return path
