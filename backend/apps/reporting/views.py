from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from django.utils import timezone
from apps.access_control.permissions import IsFinanceStaff
from apps.billing.models import Invoice, InvoiceStatus
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from apps.portal.serializers import PortalInvoiceSerializer
from .services import calculate_dashboard_metrics


class DashboardMetricsView(APIView):
    """
    Returns the 7 PRD §7.13 KPI metrics with exact database aggregations.
    Guarded by IsFinanceStaff.
    """
    permission_classes = [IsFinanceStaff]

    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        customer_id = request.query_params.get("customer_id")
        plan_name = request.query_params.get("plan_name")

        data = calculate_dashboard_metrics(
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            plan_name=plan_name,
        )
        return Response(data)


class InvoiceReportView(generics.ListAPIView):
    """Detailed filterable report of invoices for finance staff."""
    permission_classes = [IsFinanceStaff]
    serializer_class = PortalInvoiceSerializer

    def get_queryset(self):
        qs = Invoice.objects.select_related("customer", "subscription_link").all()
        status_param = self.request.query_params.get("status")
        customer_id = self.request.query_params.get("customer_id")
        is_overdue = self.request.query_params.get("is_overdue")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if status_param:
            qs = qs.filter(status=status_param)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if start_date:
            qs = qs.filter(issue_date__gte=start_date)
        if end_date:
            qs = qs.filter(issue_date__lte=end_date)
        if is_overdue and is_overdue.lower() in ["true", "1"]:
            today = timezone.now().date()
            qs = qs.filter(
                status__in=[InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID],
                due_date__lt=today,
            )

        return qs


class PaymentReportView(generics.ListAPIView):
    """Detailed filterable report of payments for finance staff."""
    permission_classes = [IsFinanceStaff]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.select_related("invoice", "customer", "recorded_by").all()
        method = self.request.query_params.get("method")
        customer_id = self.request.query_params.get("customer_id")
        is_reversed = self.request.query_params.get("is_reversed")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if method:
            qs = qs.filter(method=method)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if is_reversed is not None:
            qs = qs.filter(is_reversed=(is_reversed.lower() in ["true", "1"]))
        if start_date:
            qs = qs.filter(paid_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(paid_at__date__lte=end_date)

        return qs

