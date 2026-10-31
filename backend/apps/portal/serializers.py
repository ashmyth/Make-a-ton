from rest_framework import serializers
from apps.customers.models import Customer
from apps.subscriptions.models import Subscription
from apps.billing.models import Invoice
from apps.payments.models import Payment
from .models import CustomerRequest, RequestType


class PortalSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "id",
            "subscription_number",
            "plan_name",
            "billing_interval",
            "status",
            "is_paused",
            "start_date",
            "expiry_date",
            "next_billing_date",
            "currency",
            "created_at",
        ]
        read_only_fields = fields


class PortalInvoiceSerializer(serializers.ModelSerializer):
    subscription_number = serializers.CharField(source="subscription.subscription_number", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "subscription",
            "subscription_number",
            "issue_date",
            "due_date",
            "service_period_start",
            "service_period_end",
            "subtotal",
            "discount_total",
            "tax_total",
            "total_amount",
            "outstanding_balance",
            "currency",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class PortalPaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "invoice",
            "invoice_number",
            "amount",
            "currency",
            "method",
            "status",
            "external_reference",
            "paid_at",
        ]
        read_only_fields = fields


class CustomerRequestSerializer(serializers.ModelSerializer):
    subscription_number = serializers.CharField(source="subscription.subscription_number", read_only=True)

    class Meta:
        model = CustomerRequest
        fields = [
            "id",
            "subscription",
            "subscription_number",
            "request_type",
            "status",
            "notes",
            "staff_response",
            "created_at",
        ]
        read_only_fields = ["id", "status", "staff_response", "created_at"]

    def validate_subscription(self, value):
        # Enforce that subscription belongs to the authenticated customer
        customer = self.context["request"].user.customer
        if not customer or value.customer_id != customer.id:
            raise serializers.ValidationError("Subscription does not belong to your account.")
        return value


class PortalProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "contact_person",
            "phone",
            "billing_street",
            "billing_city",
            "billing_state",
            "billing_postal_code",
            "billing_country",
        ]

