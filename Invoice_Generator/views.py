"""FEATURE 12: staff dashboard. Review generated invoices, send, cancel, and preview.

Permissions (enforced in backend, not just hidden buttons):
  view list/detail/pdf -> Django perm  billing.view_invoice
  send / resend        -> Django perm  billing.send_invoice
  cancel               -> Django perm  billing.change_invoice
Superuser = all. Grant others via Django admin -> Groups.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Invoice, InvoiceStatus
from .services.pdf import render_invoice_pdf
from .pipeline import InvoiceSendError, send_invoice


@login_required
@permission_required("billing.view_invoice", raise_exception=True)
def invoice_list(request):
    qs = Invoice.objects.all()

    status = request.GET.get("status", "")
    if status in InvoiceStatus.values:
        qs = qs.filter(status=status)

    sent = request.GET.get("sent", "")
    if sent == "no":
        qs = qs.filter(email_sent_at__isnull=True).exclude(status=InvoiceStatus.CANCELLED)
    elif sent == "yes":
        qs = qs.filter(email_sent_at__isnull=False)

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(invoice_number__icontains=q)
            | Q(customer_name__icontains=q)
            | Q(customer_email__icontains=q)
            | Q(subscription_number__icontains=q)
        )

    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "billing/invoice_list.html", {
        "page": page,
        "statuses": InvoiceStatus.choices,
        "f_status": status, "f_sent": sent, "q": q,
        "pending_count": Invoice.objects.filter(email_sent_at__isnull=True)
                                        .exclude(status=InvoiceStatus.CANCELLED).count(),
    })


@login_required
@permission_required("billing.view_invoice", raise_exception=True)
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.prefetch_related("lines", "email_logs"), pk=pk)
    return render(request, "billing/invoice_detail.html", {"invoice": invoice})


@login_required
@permission_required("billing.view_invoice", raise_exception=True)
def invoice_pdf(request, pk):
    """Inline PDF preview so staff sees exactly what customer will get."""
    invoice = get_object_or_404(Invoice, pk=pk)
    resp = HttpResponse(render_invoice_pdf(invoice), content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{invoice.invoice_number}.pdf"'
    return resp


@login_required
@permission_required("billing.send_invoice", raise_exception=True)
@require_POST
def invoice_send(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        ok = send_invoice(invoice.pk, request.user, resend=request.POST.get("resend") == "1")
    except InvoiceSendError as exc:
        messages.error(request, str(exc))
    else:
        if ok:
            messages.success(request, f"{invoice.invoice_number} sent to {invoice.customer_email}.")
        else:
            messages.error(request, "Email failed. See send log below, then try again.")
    return redirect("billing:invoice_detail", pk=invoice.pk)


@login_required
@permission_required("billing.change_invoice", raise_exception=True)
@require_POST
def invoice_cancel(request, pk):
    """Cancel an invoice per PRD §7.9 (allowed only if no payments are allocated)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.can_cancel:
        messages.error(
            request,
            "Cannot cancel invoice: either it is already cancelled or payments have been allocated."
        )
    else:
        invoice.status = InvoiceStatus.CANCELLED
        invoice.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Invoice {invoice.invoice_number} has been cancelled.")
    return redirect("billing:invoice_detail", pk=invoice.pk)
