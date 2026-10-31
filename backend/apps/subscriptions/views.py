from datetime import timedelta
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .services import process_subscription_expiries

from .models import (
    QuotationTemplate,
    QuotationTemplateLine,
    Quotation,
    QuotationLine,
    QuotationStatus,
    Subscription,
    SubscriptionLine,
    SubscriptionStatus,
    OperationalStatus
)
from .serializers import (
    QuotationTemplateSerializer,
    CreateQuotationFromTemplateSerializer,
    ExtendQuotationSerializer,
    QuotationSerializer,
    QuotationCreateSerializer,
    SubscriptionSerializer,
    SubscriptionBillingExportSerializer,
    SubscriptionCustomerPortalSerializer,
    ConvertQuotationSerializer,
    PauseSubscriptionSerializer,
    CloseSubscriptionSerializer,
    RenewSubscriptionSerializer
)
from apps.catalog.models import StatusChoices


class QuotationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Quotation Templates.
    Supports Create, Edit, Archive, Duplicate, and Creating Quotations from templates.
    """
    permission_classes = [permissions.AllowAny]
    queryset = QuotationTemplate.objects.all().prefetch_related('lines__product', 'lines__variant', 'plan')
    serializer_class = QuotationTemplateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'all':
            queryset = queryset.filter(status=status_param)
        elif not status_param:
            queryset = queryset.filter(status=StatusChoices.ACTIVE)
        return queryset

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "Direct deletion of templates is forbidden. Use POST /archive/ instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        template = self.get_object()
        template.archive()
        serializer = self.get_serializer(template)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Deep-duplicates a template and all of its product lines.
        Zero mock: creates real new database records.
        """
        template = self.get_object()
        new_name = request.data.get('name')
        duplicated = template.duplicate(new_name=new_name)
        serializer = self.get_serializer(duplicated)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='create-quotation')
    @transaction.atomic
    def create_quotation(self, request, pk=None):
        """
        Generates a new Quotation from this template.
        Copies template values, calculates expiry, and snapshots commercial terms.
        """
        template = self.get_object()
        req_serializer = CreateQuotationFromTemplateSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)

        customer_id = req_serializer.validated_data['customer_id']
        issue_date = req_serializer.validated_data.get('issue_date') or timezone.now().date()
        notes = req_serializer.validated_data.get('notes') or template.notes

        # Calculate expiry date dynamically: issue_date + validity_days
        expiry_date = issue_date + timedelta(days=template.validity_days)

        # Generate unique quotation number
        year = issue_date.year
        count = Quotation.objects.filter(issue_date__year=year).count() + 1
        quotation_number = f"QT-{year}-{count:04d}"
        while Quotation.objects.filter(quotation_number=quotation_number).exists():
            count += 1
            quotation_number = f"QT-{year}-{count:04d}"

        # Create Quotation
        quotation = Quotation.objects.create(
            quotation_number=quotation_number,
            customer_id=customer_id,
            template=template,
            plan=template.plan,
            status=QuotationStatus.DRAFT,
            issue_date=issue_date,
            expiry_date=expiry_date,
            payment_terms=template.plan.default_payment_terms,
            notes=notes
        )

        # Copy lines and snapshot resolved prices per PRD §7.4
        for tmpl_line in template.lines.all():
            unit_price = QuotationLine.resolve_unit_price(
                plan=template.plan,
                product=tmpl_line.product,
                variant=tmpl_line.variant,
                is_primary=tmpl_line.is_primary
            )
            desc = tmpl_line.product.name
            if tmpl_line.variant:
                desc += f" ({tmpl_line.variant.attribute_name}: {tmpl_line.variant.value})"

            QuotationLine.objects.create(
                quotation=quotation,
                product=tmpl_line.product,
                variant=tmpl_line.variant,
                description=desc,
                quantity=tmpl_line.default_quantity,
                unit_price=unit_price,
                line_total=unit_price * tmpl_line.default_quantity,
                is_primary=tmpl_line.is_primary,
                sort_order=tmpl_line.sort_order
            )

        resp_serializer = QuotationSerializer(quotation)
        return Response(resp_serializer.data, status=status.HTTP_201_CREATED)


class QuotationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for customer Quotations.
    Supports creating from scratch, review workflow, confirming, extending, and cancelling quotations.
    """
    permission_classes = [permissions.AllowAny]
    queryset = Quotation.objects.all().prefetch_related('lines__product', 'lines__variant', 'plan')
    serializer_class = QuotationSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return QuotationCreateSerializer
        return QuotationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        customer_id = self.request.query_params.get('customer_id')
        status_param = self.request.query_params.get('status')

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quotation = serializer.save()
        read_serializer = QuotationSerializer(quotation)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        quotation = self.get_object()
        if quotation.status == QuotationStatus.CONFIRMED:
            return Response(
                {"error": "Confirmed quotations cannot be modified to preserve commercial terms."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "Direct deletion of quotations is forbidden. Use status transition instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Transitions quotation status from Draft to Sent."""
        quotation = self.get_object()
        try:
            quotation.send_to_customer()
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(QuotationSerializer(quotation).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Transitions quotation status to Reviewed."""
        quotation = self.get_object()
        try:
            quotation.mark_reviewed()
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(QuotationSerializer(quotation).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancels quotation."""
        quotation = self.get_object()
        reason = request.data.get('reason')
        try:
            quotation.cancel(reason=reason)
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(QuotationSerializer(quotation).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirms a quotation.
        STRICT PRD RULE:
        Prevent expired quotations from being confirmed unless extended or reissued.
        """
        quotation = self.get_object()
        confirmed_by = request.data.get('confirmed_by', 'Operations Staff')

        try:
            quotation.confirm(confirmed_by_user=confirmed_by)
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(quotation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """
        Extends the validity date of a quotation, allowing expired quotes to be reissued/confirmed.
        """
        quotation = self.get_object()
        serializer = ExtendQuotationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        days = serializer.validated_data.get('additional_days', 30)

        quotation.extend_validity(days)
        resp_serializer = self.get_serializer(quotation)
        return Response(resp_serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='convert-to-subscription')
    @transaction.atomic
    def convert_to_subscription(self, request, pk=None):
        """
        Converts a confirmed quotation into an active subscription.
        Preserves commercial snapshot and sets billing schedule.
        """
        quotation = self.get_object()
        if quotation.status != QuotationStatus.CONFIRMED:
            return Response(
                {"error": f"Only confirmed quotations can be converted to subscriptions. Current status: '{quotation.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if hasattr(quotation, 'subscription') and quotation.subscription is not None:
            return Response(
                {"error": f"Quotation {quotation.quotation_number} has already been converted to subscription {quotation.subscription.subscription_number}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ConvertQuotationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data.get('start_date') or timezone.now().date()
        expiry_date = serializer.validated_data.get('expiry_date')

        year = start_date.year
        count = Subscription.objects.filter(start_date__year=year).count() + 1
        sub_number = f"SUB-{year}-{count:04d}"
        while Subscription.objects.filter(subscription_number=sub_number).exists():
            count += 1
            sub_number = f"SUB-{year}-{count:04d}"

        subscription = Subscription.objects.create(
            subscription_number=sub_number,
            customer_id=quotation.customer_id,
            quotation=quotation,
            plan=quotation.plan,
            status=SubscriptionStatus.ACTIVE,
            is_paused=False,
            start_date=start_date,
            expiry_date=expiry_date,
            billing_anchor_date=start_date,
            next_billing_date=start_date,
            payment_terms=quotation.payment_terms or quotation.plan.default_payment_terms
        )

        for qline in quotation.lines.all():
            SubscriptionLine.objects.create(
                subscription=subscription,
                product=qline.product,
                variant=qline.variant,
                description=qline.description,
                quantity=qline.quantity,
                unit_price=qline.unit_price,
                is_primary=qline.is_primary,
                sort_order=qline.sort_order
            )

        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing the complete Subscription lifecycle.
    Supports viewing, pausing, resuming, renewing, closing, and exporting for billing.
    """
    permission_classes = [permissions.AllowAny]
    queryset = Subscription.objects.all().prefetch_related(
        'lines__product',
        'lines__variant',
        'plan',
        'predecessor',
        'successor'
    )

    def get_serializer_class(self):
        view_as = self.request.query_params.get('view_as')
        if view_as == 'customer':
            return SubscriptionCustomerPortalSerializer
        return SubscriptionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        customer_id = self.request.query_params.get('customer_id')
        status_param = self.request.query_params.get('status')
        op_status = self.request.query_params.get('operational_status')
        action_required_param = self.request.query_params.get('action_required')

        if customer_id:
            queryset = queryset.filter(
                models.Q(customer__id=customer_id) |
                models.Q(customer__customer_code=customer_id) |
                models.Q(customer_id_ref=customer_id)
            )
        if status_param:
            queryset = queryset.filter(status=status_param)
        if op_status:
            queryset = queryset.filter(operational_status=op_status)
        if action_required_param is not None:
            queryset = queryset.filter(action_required=action_required_param.lower() in ['true', '1'])

        return queryset

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "Direct deletion of subscriptions is forbidden. Subscriptions must be closed via the close action."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Pauses an active subscription.
        Strictly enforced: rejected if plan.allow_pause is False.
        """
        subscription = self.get_object()
        serializer = PauseSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')

        try:
            subscription.pause(reason=reason)
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resumes a paused subscription."""
        subscription = self.get_object()
        try:
            subscription.resume()
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """
        Renews subscription into a linked successor subscription.
        Strictly enforced: rejected if plan.allow_renewal is False.
        """
        subscription = self.get_object()
        serializer = RenewSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_start = serializer.validated_data.get('new_start_date')
        new_expiry = serializer.validated_data.get('new_expiry_date')

        try:
            successor = subscription.renew(new_start_date=new_start, new_expiry_date=new_expiry)
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(successor).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """
        Closes subscription (early cancellation or term expiry).
        Strictly enforced: rejected if early closure is requested but plan.allow_early_closure is False.
        """
        subscription = self.get_object()
        serializer = CloseSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')
        early = serializer.validated_data.get('early', False)

        try:
            subscription.close(reason=reason, early=early)
        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='due-for-billing')
    def due_for_billing(self, request):
        """
        CRITICAL INTEGRATION ENDPOINT FOR TEAMMATE 3 (BILLING ENGINE).
        Returns active & running subscriptions due for recurring invoice generation.
        STRICT RULE: Paused and Closed subscriptions are NEVER returned for billing.
        """
        as_of_str = request.query_params.get('as_of')
        if as_of_str:
            try:
                as_of_date = timezone.datetime.strptime(as_of_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format for 'as_of'. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            as_of_date = timezone.now().date()

        # Query eligible subscriptions:
        # 1. status must be ACTIVE
        # 2. operational_status must be RUNNING (PAUSED subscriptions are excluded!)
        # 3. next_billing_date <= as_of_date
        # 4. start_date <= as_of_date
        # 5. if expiry_date set, next_billing_date <= expiry_date and expiry_date >= as_of_date
        # 6. action_required must be False (billing halts on expired action-required subscriptions per PRD §7.7)
        eligible_subs = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            is_paused=False,
            action_required=False,
            start_date__lte=as_of_date,
            next_billing_date__lte=as_of_date
        ).filter(
            models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gte=as_of_date)
        ).prefetch_related('lines__product', 'lines__variant', 'plan')

        export_serializer = SubscriptionBillingExportSerializer(eligible_subs, many=True)
        return Response(export_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='sweep-expiries')
    def sweep_expiries(self, request):
        """
        Executes an automated sweep of expired subscriptions:
        - Subscriptions under plans with auto_close_at_expiry=True are automatically closed.
        - Subscriptions under plans with auto_close_at_expiry=False enter the action-required queue
          and halt further billing (PRD §7.7).
        """
        as_of_str = request.data.get('as_of') or request.query_params.get('as_of')
        if as_of_str:
            try:
                as_of_date = timezone.datetime.strptime(as_of_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format for 'as_of'. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            as_of_date = timezone.now().date()

        result = process_subscription_expiries(as_of_date=as_of_date)
        return Response(result, status=status.HTTP_200_OK)
