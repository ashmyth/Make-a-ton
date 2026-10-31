from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from apps.access_control.permissions import IsFinanceStaff
from .models import Payment
from .serializers import (
    PaymentSerializer,
    RecordPaymentInputSerializer,
    ReversePaymentInputSerializer,
)
from .services import record_payment, reverse_payment


class PaymentListCreateView(generics.ListCreateAPIView):
    """
    GET: List all recorded payments with optional filters (guarded by IsFinanceStaff).
    POST: Record a new payment against a confirmed invoice (guarded by IsFinanceStaff).
    """
    permission_classes = [IsFinanceStaff]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.select_related("invoice", "customer", "recorded_by").all()
        invoice_id = self.request.query_params.get("invoice_id")
        customer_id = self.request.query_params.get("customer_id")
        method = self.request.query_params.get("method")
        status_param = self.request.query_params.get("status")
        is_reversed = self.request.query_params.get("is_reversed")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if invoice_id:
            qs = qs.filter(invoice_id=invoice_id)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if method:
            qs = qs.filter(method=method)
        if status_param:
            qs = qs.filter(status=status_param)
        if is_reversed is not None:
            qs = qs.filter(is_reversed=(is_reversed.lower() in ["true", "1"]))
        if start_date:
            qs = qs.filter(paid_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(paid_at__date__lte=end_date)

        return qs

    def create(self, request, *args, **kwargs):
        input_serializer = RecordPaymentInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        try:
            payment = record_payment(
                invoice_id=data["invoice_id"],
                amount=data["amount"],
                method=data["method"],
                recorded_by=request.user,
                idempotency_key=data["idempotency_key"],
                external_reference=data.get("external_reference", ""),
                notes=data.get("notes", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentDetailView(generics.RetrieveAPIView):
    """Retrieve full details of a single payment."""
    permission_classes = [IsFinanceStaff]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("invoice", "customer", "recorded_by").all()
    lookup_field = "id"


class PaymentReverseView(APIView):
    """Reverse an existing payment (Audited reversal, PAY-04)."""
    permission_classes = [IsFinanceStaff]

    def post(self, request, id, *args, **kwargs):
        input_serializer = ReversePaymentInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        reason = input_serializer.validated_data["reason"]

        try:
            payment = reverse_payment(
                payment_id=id,
                reversed_by=request.user,
                reason=reason,
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)

