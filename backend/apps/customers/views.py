from django.db import IntegrityError, transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

try:
    from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
except ImportError:
    def extend_schema(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

    class OpenApiResponse:
        def __init__(self, *args, **kwargs):
            pass

    class OpenApiParameter:
        def __init__(self, *args, **kwargs):
            pass

from apps.access_control.permissions import (
    CustomerDataIsolation,
    IsCustomerUser,
    IsOperationsStaff,
    IsStaffUser,
)
from apps.access_control.roles import UserRole
from apps.audit.models import AuditAction
from apps.audit.services import diff_fields, record_audit

from .models import Customer
from .serializers import CUSTOMER_EDITABLE_FIELDS, CustomerSerializer, LinkPortalUserSerializer


class CustomerViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Customer CRM. There is deliberately no DELETE: customers are archived."""

    serializer_class = CustomerSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["display_name", "customer_code", "email", "contact_person", "tax_identifier"]
    ordering_fields = ["created_at", "display_name", "customer_code"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action == "list":
            classes = [IsStaffUser]
        elif self.action in {"create", "archive", "link_portal"}:
            classes = [IsOperationsStaff]
        elif self.action == "my_profile":
            classes = [IsCustomerUser]
        else:  # retrieve, partial_update
            classes = [CustomerDataIsolation]
        return [cls() for cls in classes]

    def get_queryset(self):
        queryset = Customer.objects.select_related("portal_user")
        if self.action == "list":
            params = self.request.query_params
            if value := params.get("status"):
                if value not in Customer.Status.values:
                    raise ValidationError({"status": f"Use one of {Customer.Status.values}."})
                queryset = queryset.filter(status=value)
            if value := params.get("customer_type"):
                if value not in Customer.CustomerType.values:
                    raise ValidationError(
                        {"customer_type": f"Use one of {Customer.CustomerType.values}."}
                    )
                queryset = queryset.filter(customer_type=value)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("status", enum=Customer.Status.values, required=False),
            OpenApiParameter("customer_type", enum=Customer.CustomerType.values, required=False),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            customer = Customer.objects.create_with_code(**serializer.validated_data)
            record_audit(
                action=AuditAction.CUSTOMER_CREATED,
                actor=request.user,
                entity_type="Customer",
                entity_id=customer.pk,
                details={
                    "customer_code": customer.customer_code,
                    "display_name": customer.display_name,
                },
                request=request,
            )
        return Response(self.get_serializer(customer).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        customer = self.get_object()
        if request.user.role == UserRole.CUSTOMER:
            forbidden = sorted(set(request.data) - CUSTOMER_EDITABLE_FIELDS)
            if forbidden:
                raise PermissionDenied(
                    f"Customers cannot modify these fields: {', '.join(forbidden)}."
                )
        serializer = self.get_serializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            before = {f: getattr(customer, f) for f in serializer.validated_data}
            customer = serializer.save()
            changes = diff_fields(before, {f: getattr(customer, f) for f in before})
            if changes:
                record_audit(
                    action=AuditAction.CUSTOMER_UPDATED,
                    actor=request.user,
                    entity_type="Customer",
                    entity_id=customer.pk,
                    details={"changes": changes},
                    request=request,
                )
        return Response(self.get_serializer(customer).data)

    @extend_schema(responses=CustomerSerializer)
    @action(detail=False, methods=["get"], url_path="my-profile")
    def my_profile(self, request):
        customer = request.user.customer
        if customer is None:
            raise NotFound("No customer record is linked to this account.")
        return Response(self.get_serializer(customer).data)

    @extend_schema(
        request=None,
        responses={200: CustomerSerializer, 409: OpenApiResponse(description="Already archived")},
    )
    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        with transaction.atomic():
            customer = Customer.objects.select_for_update().get(pk=self.get_object().pk)
            if customer.status == Customer.Status.ARCHIVED:
                return Response(
                    {"detail": "Customer is already archived."}, status=status.HTTP_409_CONFLICT
                )
            customer.status = Customer.Status.ARCHIVED
            customer.save(update_fields=["status", "updated_at"])
            record_audit(
                action=AuditAction.CUSTOMER_ARCHIVED,
                actor=request.user,
                entity_type="Customer",
                entity_id=customer.pk,
                details={"customer_code": customer.customer_code},
                request=request,
            )
        return Response(self.get_serializer(customer).data)

    @extend_schema(
        request=LinkPortalUserSerializer,
        responses={200: CustomerSerializer, 400: OpenApiResponse(description="Invalid user")},
    )
    @action(detail=True, methods=["post"], url_path="link-portal")
    def link_portal(self, request, pk=None):
        serializer = LinkPortalUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        portal_user = serializer.context["portal_user"]
        try:
            with transaction.atomic():
                customer = Customer.objects.select_for_update().get(pk=self.get_object().pk)
                if customer.portal_user_id is not None:
                    return Response(
                        {"detail": "Customer already has a linked portal user."},
                        status=status.HTTP_409_CONFLICT,
                    )
                customer.portal_user = portal_user
                customer.save(update_fields=["portal_user", "updated_at"])
                record_audit(
                    action=AuditAction.CUSTOMER_PORTAL_LINKED,
                    actor=request.user,
                    entity_type="Customer",
                    entity_id=customer.pk,
                    details={"portal_user_id": str(portal_user.pk), "email": portal_user.email},
                    request=request,
                )
        except IntegrityError as exc:
            raise ValidationError({"user_id": "User is already linked to a customer."}) from exc
        return Response(self.get_serializer(customer).data)

