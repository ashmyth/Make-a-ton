from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.access_control.permissions import IsAdministrator
from apps.access_control.roles import UserRole
from apps.accounts.services import revoke_user_sessions
from apps.audit.models import AuditAction
from apps.audit.services import diff_fields, record_audit

from .serializers import StaffCreateSerializer, StaffSerializer, StaffUpdateSerializer

User = get_user_model()


class StaffViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Administrator-only staff account lifecycle (soft deactivation, no deletion)."""

    permission_classes = [IsAdministrator]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = User.objects.exclude(role=UserRole.CUSTOMER).order_by("email")
        params = self.request.query_params
        if role := params.get("role"):
            queryset = queryset.filter(role=role)
        if (active := params.get("is_active")) is not None:
            if active.lower() not in {"true", "false"}:
                raise ValidationError({"is_active": "Use true or false."})
            queryset = queryset.filter(is_active=active.lower() == "true")
        if search := params.get("search"):
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return StaffCreateSerializer
        if self.action == "partial_update":
            return StaffUpdateSerializer
        return StaffSerializer

    @extend_schema(request=StaffCreateSerializer, responses={201: StaffSerializer})
    def create(self, request, *args, **kwargs):
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                user = serializer.save()
                record_audit(
                    action=AuditAction.STAFF_CREATED,
                    actor=request.user,
                    entity_type="User",
                    entity_id=user.pk,
                    details={"email": user.email, "role": user.role},
                    request=request,
                )
        except IntegrityError as exc:
            raise ValidationError({"email": ["A user with this email already exists."]}) from exc
        return Response(StaffSerializer(user).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=StaffUpdateSerializer, responses={200: StaffSerializer})
    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = StaffUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if request.user.pk == user.pk and "role" in serializer.validated_data:
            raise ValidationError({"role": "You cannot change your own role."})
        with transaction.atomic():
            before = {f: getattr(user, f) for f in serializer.validated_data}
            serializer.save()
            changes = diff_fields(before, {f: getattr(user, f) for f in before})
            if changes:
                record_audit(
                    action=AuditAction.STAFF_UPDATED,
                    actor=request.user,
                    entity_type="User",
                    entity_id=user.pk,
                    details={"changes": changes},
                    request=request,
                )
        return Response(StaffSerializer(user).data)

    @extend_schema(
        request=None,
        responses={200: StaffSerializer, 400: OpenApiResponse(description="Not allowed")},
    )
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError({"detail": "You cannot deactivate your own account."})
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.is_active:
                return Response(
                    {"detail": "Account is already inactive."}, status=status.HTTP_409_CONFLICT
                )
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])
            revoke_user_sessions(user)
            record_audit(
                action=AuditAction.STAFF_DEACTIVATED,
                actor=request.user,
                entity_type="User",
                entity_id=user.pk,
                details={"email": user.email},
                request=request,
            )
        return Response(StaffSerializer(user).data)

    @extend_schema(request=None, responses={200: StaffSerializer})
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if user.is_active:
                return Response(
                    {"detail": "Account is already active."}, status=status.HTTP_409_CONFLICT
                )
            user.is_active = True
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(
                update_fields=["is_active", "failed_login_attempts", "locked_until", "updated_at"]
            )
            record_audit(
                action=AuditAction.STAFF_ACTIVATED,
                actor=request.user,
                entity_type="User",
                entity_id=user.pk,
                details={"email": user.email},
                request=request,
            )
        return Response(StaffSerializer(user).data)
