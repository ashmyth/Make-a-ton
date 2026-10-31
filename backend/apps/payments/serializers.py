from decimal import Decimal
from rest_framework import serializers
from .models import Payment, PaymentMethod, PaymentStatus


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    customer_name = serializers.CharField(source="customer.display_name", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "invoice",
            "invoice_number",
            "customer",
            "customer_name",
            "recorded_by",
            "recorded_by_name",
            "amount",
            "currency",
            "method",
            "status",
            "idempotency_key",
            "external_reference",
            "notes",
            "paid_at",
            "is_reversed",
            "reversed_at",
            "reversal_reason",
            "created_at",
        ]
        read_only_fields = fields


class RecordPaymentInputSerializer(serializers.Serializer):
    invoice_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"), required=True)
    method = serializers.ChoiceField(choices=PaymentMethod.choices, default=PaymentMethod.BANK_TRANSFER)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    external_reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ReversePaymentInputSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=True, min_length=3)
