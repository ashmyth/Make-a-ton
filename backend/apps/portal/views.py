from decimal import Decimal
from django.db.models import Sum
from django.http import HttpResponse
from django.utils.html import escape
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.access_control.permissions import IsCustomerUser, CustomerDataIsolation
from apps.billing.models import Invoice, InvoiceStatus
from apps.subscriptions.models import Subscription, SubscriptionStatus
from apps.payments.models import Payment
from apps.customers.models import Customer
from .models import CustomerRequest
from .serializers import (
    PortalSubscriptionSerializer,
    PortalInvoiceSerializer,
    PortalPaymentSerializer,
    CustomerRequestSerializer,
    PortalProfileUpdateSerializer,
)


class PortalOverviewView(APIView):
    """Returns high-level summary metrics for the authenticated customer portal."""
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]

    def get(self, request):
        customer = request.user.customer
        if not customer:
            return Response({"detail": "No customer profile linked to this account."}, status=status.HTTP_404_NOT_FOUND)

        active_subs = Subscription.objects.filter(customer=customer, status=SubscriptionStatus.ACTIVE).count()
        unpaid_invoices_qs = Invoice.objects.filter(
            customer=customer,
            status__in=[InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID],
        )
        unpaid_count = unpaid_invoices_qs.count()
        outstanding_sum = unpaid_invoices_qs.aggregate(total=Sum("outstanding_balance"))["total"] or Decimal("0.00")

        recent_invoices = Invoice.objects.filter(customer=customer).exclude(status=InvoiceStatus.DRAFT)[:3]
        recent_payments = Payment.objects.filter(customer=customer, is_reversed=False)[:3]

        return Response({
            "customer": {
                "id": customer.id,
                "customer_code": customer.customer_code,
                "display_name": customer.display_name,
                "contact_person": customer.contact_person,
                "email": customer.email,
                "phone": customer.phone,
                "full_billing_address": customer.full_billing_address,
                "payment_terms": customer.payment_terms,
            },
            "metrics": {
                "active_subscriptions": active_subs,
                "unpaid_invoices_count": unpaid_count,
                "total_outstanding_balance": str(outstanding_sum),
                "currency": "INR",
            },
            "recent_invoices": PortalInvoiceSerializer(recent_invoices, many=True).data,
            "recent_payments": PortalPaymentSerializer(recent_payments, many=True).data,
        })


class PortalSubscriptionListView(generics.ListAPIView):
    """Lists subscriptions owned by the logged-in customer."""
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
    serializer_class = PortalSubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(customer_id=self.request.user.customer_id)


class PortalInvoiceListView(generics.ListAPIView):
    """Lists non-draft invoices issued to the logged-in customer."""
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
    serializer_class = PortalInvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(
            customer_id=self.request.user.customer_id
        ).exclude(status=InvoiceStatus.DRAFT)


class PortalInvoiceDetailView(generics.RetrieveAPIView):
    """Retrieves a single invoice, preventing IDOR via CustomerDataIsolation."""
    permission_classes = [permissions.IsAuthenticated, CustomerDataIsolation]
    serializer_class = PortalInvoiceSerializer
    queryset = Invoice.objects.all()
    lookup_field = "id"


class PortalInvoiceDownloadView(APIView):
    """Generates a complete, downloadable printable invoice HTML document."""
    permission_classes = [permissions.IsAuthenticated, CustomerDataIsolation]

    def get(self, request, id):
        try:
            invoice = Invoice.objects.select_related("customer", "subscription_link").get(id=id)
        except Invoice.DoesNotExist:
            return Response({"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, invoice)

        # Sanitize and HTML-escape all user-controlled customer and invoice data to prevent XSS (SEC-01)
        esc_invoice_number = escape(invoice.invoice_number)
        esc_status = escape(invoice.status)
        esc_status_display = escape(invoice.status.replace('_', ' '))
        esc_display_name = escape(invoice.customer.display_name if invoice.customer else "")
        esc_contact_person = escape(invoice.customer.contact_person if invoice.customer else "")
        esc_billing_address = escape(invoice.customer.full_billing_address if invoice.customer else "")
        esc_email = escape(invoice.customer.email if invoice.customer else "")
        esc_tax_id = escape(invoice.customer.tax_identifier if invoice.customer and invoice.customer.tax_identifier else "N/A")
        esc_issue_date = escape(str(invoice.issue_date))
        esc_due_date = escape(str(invoice.due_date))
        esc_sub_num = escape(invoice.subscription.subscription_number if invoice.subscription else "Direct")
        esc_payment_terms = escape(invoice.customer.payment_terms if invoice.customer else "NET_30")
        esc_plan_name = escape(invoice.subscription.plan_name if invoice.subscription else "Commercial Plan")
        esc_period_start = escape(str(invoice.service_period_start or invoice.issue_date))
        esc_period_end = escape(str(invoice.service_period_end or invoice.due_date))
        esc_currency = escape(invoice.currency)
        esc_subtotal = escape(str(invoice.subtotal))
        esc_discount = escape(str(invoice.discount_total))
        esc_tax = escape(str(invoice.tax_total))
        esc_total = escape(str(invoice.total_amount))
        esc_balance = escape(str(invoice.outstanding_balance))
        balance_color = "#cc0000" if invoice.outstanding_balance > 0 else "#008800"

        # Build clean printable invoice HTML with industrial styling
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Invoice {esc_invoice_number}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; color: #000000; margin: 40px; line-height: 1.4; }}
  .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #000000; padding-bottom: 20px; margin-bottom: 30px; }}
  .brand {{ font-size: 28px; font-weight: 700; letter-spacing: -1px; }}
  .brand-badge {{ background: #fff313; color: #000000; padding: 2px 8px; border-radius: 4px; font-size: 14px; }}
  .invoice-title {{ text-align: right; font-size: 20px; font-weight: 600; text-transform: uppercase; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 30px; }}
  .meta-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #666666; margin-bottom: 4px; }}
  .meta-val {{ font-size: 14px; font-weight: 500; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 30px; }}
  th {{ background: #eeeeee; text-align: left; padding: 10px 12px; font-size: 12px; text-transform: uppercase; border-bottom: 1px solid #000000; }}
  td {{ padding: 12px; border-bottom: 1px solid #dddddd; font-size: 14px; }}
  .totals {{ margin-left: auto; width: 320px; }}
  .totals-row {{ display: flex; justify-content: space-between; padding: 6px 0; font-size: 14px; }}
  .totals-row.grand {{ font-size: 18px; font-weight: 700; border-top: 2px solid #000000; border-bottom: 2px solid #000000; padding: 10px 0; margin-top: 8px; }}
  .status-badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600; text-transform: uppercase; background: #000000; color: #ffffff; }}
  .status-paid {{ background: #008844; }}
  .status-partially_paid {{ background: #ffaa00; color: #000000; }}
  .footer {{ margin-top: 60px; font-size: 12px; color: #888888; border-top: 1px solid #eeeeee; padding-top: 20px; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <div class="brand">Brightloop <span class="brand-badge">Subscription Platform</span></div>
      <div style="margin-top: 8px; color: #444444; font-size: 13px;">Automated Subscription & Invoicing Engine</div>
    </div>
    <div>
      <div class="invoice-title">Invoice #{esc_invoice_number}</div>
      <div style="text-align: right; margin-top: 6px;">
        <span class="status-badge status-{esc_status}">{esc_status_display}</span>
      </div>
    </div>
  </div>

  <div class="grid">
    <div>
      <div class="meta-label">Billed To</div>
      <div class="meta-val" style="font-size: 16px; font-weight: 700;">{esc_display_name}</div>
      <div class="meta-val">{esc_contact_person}</div>
      <div class="meta-val">{esc_billing_address}</div>
      <div class="meta-val">{esc_email}</div>
      <div class="meta-val">Tax ID: {esc_tax_id}</div>
    </div>
    <div>
      <div class="meta-label">Invoice Details</div>
      <div class="meta-val">Issue Date: <strong>{esc_issue_date}</strong></div>
      <div class="meta-val">Due Date: <strong>{esc_due_date}</strong></div>
      <div class="meta-val">Subscription: <strong>{esc_sub_num}</strong></div>
      <div class="meta-val">Payment Terms: <strong>{esc_payment_terms}</strong></div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Description</th>
        <th>Service Period</th>
        <th style="text-align: right;">Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Subscription Billing — {esc_plan_name}</td>
        <td>{esc_period_start} to {esc_period_end}</td>
        <td style="text-align: right;">{esc_currency} {esc_subtotal}</td>
      </tr>
    </tbody>
  </table>

  <div class="totals">
    <div class="totals-row">
      <span>Subtotal:</span>
      <span>{esc_currency} {esc_subtotal}</span>
    </div>
    <div class="totals-row">
      <span>Discounts:</span>
      <span>- {esc_currency} {esc_discount}</span>
    </div>
    <div class="totals-row">
      <span>Tax:</span>
      <span>+ {esc_currency} {esc_tax}</span>
    </div>
    <div class="totals-row grand">
      <span>Total Amount:</span>
      <span>{esc_currency} {esc_total}</span>
    </div>
    <div class="totals-row" style="color: {balance_color}; font-weight: 600; margin-top: 6px;">
      <span>Remaining Balance:</span>
      <span>{esc_currency} {esc_balance}</span>
    </div>
  </div>

  <div class="footer">
    Thank you for your business. For questions or payment inquiries, please refer to your portal at Brightloop.
  </div>
</body>
</html>"""
        response = HttpResponse(html_content, content_type="text/html")
        response["Content-Disposition"] = f'attachment; filename="Invoice_{invoice.invoice_number}.html"'
        return response


class PortalPaymentListView(generics.ListAPIView):
    """Lists payments made by the logged-in customer."""
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
    serializer_class = PortalPaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            customer_id=self.request.user.customer_id,
            is_reversed=False,
        )


class PortalRequestListCreateView(generics.ListCreateAPIView):
    """Allows customers to submit pause, cancel, or renew requests."""
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
    serializer_class = CustomerRequestSerializer

    def get_queryset(self):
        return CustomerRequest.objects.filter(customer_id=self.request.user.customer_id)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user.customer)


class PortalProfileView(APIView):
    """Allows customer to view their CRM profile and edit permitted fields only (PRD §4.2)."""
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]

    def get(self, request):
        customer = request.user.customer
        if not customer:
            return Response({"detail": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": customer.id,
            "customer_code": customer.customer_code,
            "customer_type": customer.customer_type,
            "display_name": customer.display_name,
            "contact_person": customer.contact_person,
            "email": customer.email,
            "phone": customer.phone,
            "billing_street": customer.billing_street,
            "billing_city": customer.billing_city,
            "billing_state": customer.billing_state,
            "billing_postal_code": customer.billing_postal_code,
            "billing_country": customer.billing_country,
            "full_billing_address": customer.full_billing_address,
            "tax_identifier": customer.tax_identifier,
            "payment_terms": customer.payment_terms,
            "status": customer.status,
        })

    def patch(self, request):
        customer = request.user.customer
        if not customer:
            return Response({"detail": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PortalProfileUpdateSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

