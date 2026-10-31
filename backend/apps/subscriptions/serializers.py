from decimal import Decimal
from rest_framework import serializers
from .models import (
    QuotationTemplate,
    QuotationTemplateLine,
    Quotation,
    QuotationLine,
    QuotationStatus
)
from apps.catalog.models import Product, ProductVariant, SubscriptionPlan


class QuotationTemplateLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_value = serializers.CharField(source='variant.value', read_only=True, default=None)

    class Meta:
        model = QuotationTemplateLine
        fields = [
            'id',
            'product',
            'product_name',
            'variant',
            'variant_value',
            'default_quantity',
            'is_primary',
            'sort_order'
        ]

    def validate(self, attrs):
        product = attrs.get('product')
        variant = attrs.get('variant')
        if variant and product and variant.product_id != product.id:
            raise serializers.ValidationError({
                'variant': 'The selected variant does not belong to the selected product.'
            })
        return attrs


class QuotationTemplateSerializer(serializers.ModelSerializer):
    lines = QuotationTemplateLineSerializer(many=True, required=False)
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = QuotationTemplate
        fields = [
            'id',
            'name',
            'plan',
            'plan_name',
            'validity_days',
            'notes',
            'status',
            'lines',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'plan_name']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        template = QuotationTemplate.objects.create(**validated_data)
        for line_data in lines_data:
            QuotationTemplateLine.objects.create(template=template, **line_data)
        return template

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            # Atomic update of template lines
            instance.lines.all().delete()
            for line_data in lines_data:
                QuotationTemplateLine.objects.create(template=instance, **line_data)
        return instance


class CreateQuotationFromTemplateSerializer(serializers.Serializer):
    """
    Request serializer for generating a new live Quotation from a QuotationTemplate.
    """
    customer_id = serializers.CharField(max_length=100, required=True, help_text="Customer ID (from T1)")
    issue_date = serializers.DateField(required=False, help_text="Issue date (defaults to today)")
    notes = serializers.CharField(required=False, allow_blank=True)


class ExtendQuotationSerializer(serializers.Serializer):
    """
    Request serializer to extend validity on an expired or active quotation.
    """
    additional_days = serializers.IntegerField(min_value=1, default=30, help_text="Number of additional days to extend validity")


class QuotationLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_value = serializers.CharField(source='variant.value', read_only=True, default=None)

    class Meta:
        model = QuotationLine
        fields = [
            'id',
            'product',
            'product_name',
            'variant',
            'variant_value',
            'description',
            'quantity',
            'unit_price',
            'line_total',
            'is_primary',
            'sort_order'
        ]
        read_only_fields = ['id', 'line_total', 'product_name', 'variant_value']


class QuotationSerializer(serializers.ModelSerializer):
    lines = QuotationLineSerializer(many=True, read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Quotation
        fields = [
            'id',
            'quotation_number',
            'customer_id',
            'template',
            'plan',
            'plan_name',
            'status',
            'issue_date',
            'expiry_date',
            'is_expired',
            'total_amount',
            'payment_terms',
            'notes',
            'confirmed_by',
            'confirmed_at',
            'lines',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'is_expired',
            'total_amount',
            'confirmed_by',
            'confirmed_at',
            'created_at',
            'updated_at'
        ]



from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from apps.catalog.models import StatusChoices


class QuotationLineCreateInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(status=StatusChoices.ACTIVE),
        help_text="Active product ID"
    )
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(status=StatusChoices.ACTIVE),
        required=False,
        allow_null=True,
        help_text="Active product variant ID (optional)"
    )
    quantity = serializers.IntegerField(min_value=1, default=1, help_text="Line quantity (>= 1)")
    is_primary = serializers.BooleanField(default=False, help_text="True if primary product line")
    sort_order = serializers.IntegerField(min_value=0, default=0)

    def validate(self, attrs):
        product = attrs.get('product')
        variant = attrs.get('variant')
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({
                'variant': 'The selected variant does not belong to the selected product.'
            })
        return attrs


class QuotationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a quotation from scratch with custom lines.
    Validates minimum quantities, active status, and resolves pricing snapshots.
    """
    customer_id = serializers.CharField(max_length=100, required=True, help_text="Customer ID")
    plan = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.filter(status=StatusChoices.ACTIVE),
        help_text="Active subscription plan"
    )
    issue_date = serializers.DateField(required=False, help_text="Issue date (defaults to today)")
    validity_days = serializers.IntegerField(min_value=1, required=False, default=30)
    payment_terms = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = QuotationLineCreateInputSerializer(many=True, required=True)

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("Quotation must have at least one billable line item.")
        return lines

    def validate(self, attrs):
        plan = attrs.get('plan')
        lines = attrs.get('lines', [])
        primary_qty = sum((item['quantity'] for item in lines if item.get('is_primary', False)), 0)
        if primary_qty < plan.min_quantity:
            raise serializers.ValidationError({
                'lines': f"Plan '{plan.name}' requires a minimum quantity of {plan.min_quantity}. Currently primary quantity is {primary_qty}."
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        plan = validated_data['plan']
        customer_id = validated_data['customer_id']
        issue_date = validated_data.get('issue_date') or timezone.now().date()
        validity_days = validated_data.get('validity_days', 30)
        payment_terms = validated_data.get('payment_terms') or plan.default_payment_terms
        notes = validated_data.get('notes', '')

        expiry_date = issue_date + timedelta(days=validity_days)

        year = issue_date.year
        count = Quotation.objects.filter(issue_date__year=year).count() + 1
        quotation_number = f"QT-{year}-{count:04d}"
        while Quotation.objects.filter(quotation_number=quotation_number).exists():
            count += 1
            quotation_number = f"QT-{year}-{count:04d}"

        quotation = Quotation.objects.create(
            quotation_number=quotation_number,
            customer_id=customer_id,
            plan=plan,
            status=QuotationStatus.DRAFT,
            issue_date=issue_date,
            expiry_date=expiry_date,
            payment_terms=payment_terms,
            notes=notes
        )

        for item in lines_data:
            product = item['product']
            variant = item.get('variant')
            quantity = item.get('quantity', 1)
            is_primary = item.get('is_primary', False)
            sort_order = item.get('sort_order', 0)

            unit_price = QuotationLine.resolve_unit_price(
                plan=plan,
                product=product,
                variant=variant,
                is_primary=is_primary
            )
            desc = product.name
            if variant:
                desc += f" ({variant.attribute_name}: {variant.value})"

            QuotationLine.objects.create(
                quotation=quotation,
                product=product,
                variant=variant,
                description=desc,
                quantity=quantity,
                unit_price=unit_price,
                line_total=unit_price * quantity,
                is_primary=is_primary,
                sort_order=sort_order
            )

        return quotation



from .models import Subscription, SubscriptionLine, SubscriptionStatus, OperationalStatus


class SubscriptionLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_value = serializers.CharField(source='variant.value', read_only=True, default=None)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SubscriptionLine
        fields = [
            'id',
            'product',
            'product_name',
            'variant',
            'variant_value',
            'description',
            'quantity',
            'unit_price',
            'line_total',
            'is_primary',
            'sort_order'
        ]
        read_only_fields = ['id', 'line_total', 'product_name', 'variant_value']


class SubscriptionSerializer(serializers.ModelSerializer):
    customer_id = serializers.SerializerMethodField()
    lines = SubscriptionLineSerializer(many=True, read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    billing_interval = serializers.CharField(source='plan.billing_interval', read_only=True)
    predecessor_number = serializers.CharField(source='predecessor.subscription_number', read_only=True, default=None)
    successor_number = serializers.CharField(source='successor.subscription_number', read_only=True, default=None)
    total_recurring_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    def get_customer_id(self, obj):
        if obj.customer:
            return str(obj.customer.id)
        return obj.customer_id_ref

    class Meta:
        model = Subscription
        fields = [
            'id',
            'subscription_number',
            'customer_id',
            'quotation',
            'plan',
            'plan_name',
            'billing_interval',
            'status',
            'operational_status',
            'start_date',
            'expiry_date',
            'billing_anchor_date',
            'next_billing_date',
            'last_billed_period_end',
            'payment_terms',
            'pause_date',
            'pause_reason',
            'resume_date',
            'closure_date',
            'closure_reason',
            'action_required',
            'action_required_reason',
            'predecessor',
            'predecessor_number',
            'successor',
            'successor_number',
            'total_recurring_amount',
            'lines',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class SubscriptionBillingLineExportSerializer(serializers.ModelSerializer):
    subscription_line_id = serializers.UUIDField(source='id')
    product_id = serializers.UUIDField(source='product.id')
    variant_id = serializers.UUIDField(source='variant.id', default=None, allow_null=True)

    class Meta:
        model = SubscriptionLine
        fields = [
            'subscription_line_id',
            'product_id',
            'variant_id',
            'description',
            'quantity',
            'unit_price',
            'is_primary'
        ]


class SubscriptionBillingExportSerializer(serializers.ModelSerializer):
    """
    DATA CONTRACT FOR TEAMMATE 3 (RECURRING BILLING ENGINE).
    Conforms directly to the shared SubscriptionBillingExport OpenAPI schema.
    """
    customer_id = serializers.SerializerMethodField()
    subscription_id = serializers.UUIDField(source='id')
    plan_id = serializers.UUIDField(source='plan.id')
    billing_interval = serializers.CharField(source='plan.billing_interval')
    lines = SubscriptionBillingLineExportSerializer(many=True, read_only=True)

    def get_customer_id(self, obj):
        if obj.customer:
            return str(obj.customer.id)
        return obj.customer_id_ref

    class Meta:
        model = Subscription
        fields = [
            'subscription_id',
            'subscription_number',
            'customer_id',
            'plan_id',
            'status',
            'operational_status',
            'billing_anchor_date',
            'next_billing_date',
            'billing_interval',
            'start_date',
            'expiry_date',
            'payment_terms',
            'lines'
        ]


class SubscriptionCustomerPortalSerializer(serializers.ModelSerializer):
    """
    DATA CONTRACT FOR TEAMMATE 4 (CUSTOMER PORTAL).
    Provides customer-facing visibility with internal cost_price strictly stripped.
    """
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    billing_interval = serializers.CharField(source='plan.billing_interval', read_only=True)
    total_recurring_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    lines = SubscriptionLineSerializer(many=True, read_only=True)
    successor_id = serializers.UUIDField(source='successor.id', read_only=True, default=None)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'subscription_number',
            'plan_name',
            'billing_interval',
            'status',
            'operational_status',
            'start_date',
            'expiry_date',
            'next_billing_date',
            'payment_terms',
            'total_recurring_amount',
            'successor_id',
            'lines'
        ]
        read_only_fields = fields


class ConvertQuotationSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False, help_text="Effective start date (defaults to today)")
    expiry_date = serializers.DateField(required=False, help_text="Contract term end date (optional)")


class PauseSubscriptionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, help_text="Operational pause reason")


class CloseSubscriptionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, help_text="Closure reason")
    early = serializers.BooleanField(default=False, help_text="Whether this is an early termination")


class RenewSubscriptionSerializer(serializers.Serializer):
    new_start_date = serializers.DateField(required=False, help_text="Start date for successor subscription")
    new_expiry_date = serializers.DateField(required=False, help_text="Expiry date for successor subscription")
