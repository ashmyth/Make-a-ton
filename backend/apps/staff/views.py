from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

try:
    from drf_spectacular.utils import OpenApiResponse, extend_schema
except ImportError:
    def extend_schema(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

    class OpenApiResponse:
        def __init__(self, *args, **kwargs):
            pass

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
        if self.action in {"partial_update", "update"}:
            return StaffUpdateSerializer
        return StaffSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        record_audit(
            action=AuditAction.STAFF_CREATED,
            actor=self.request.user,
            entity_type="User",
            entity_id=user.pk,
            details={"email": user.email, "role": user.role},
            request=self.request,
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        before = {"role": instance.role, "first_name": instance.first_name, "last_name": instance.last_name}
        user = serializer.save()
        after = {"role": user.role, "first_name": user.first_name, "last_name": user.last_name}
        changes = diff_fields(before, after)
        if changes:
            record_audit(
                action=AuditAction.STAFF_UPDATED,
                actor=self.request.user,
                entity_type="User",
                entity_id=user.pk,
                details={"changes": changes},
                request=self.request,
            )

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """Soft-deactivate a staff user and immediately revoke their active sessions."""
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError({"detail": "Administrators cannot deactivate themselves."})
        if not user.is_active:
            return Response(StaffSerializer(user).data)

        with transaction.atomic():
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])
            revoked = revoke_user_sessions(user)
            record_audit(
                action=AuditAction.STAFF_DEACTIVATED,
                actor=request.user,
                entity_type="User",
                entity_id=user.pk,
                details={"sessions_revoked": revoked},
                request=request,
            )
        return Response(StaffSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        """Re-activate a previously deactivated staff user."""
        user = self.get_object()
        if user.is_active:
            return Response(StaffSerializer(user).data)

        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        record_audit(
            action=AuditAction.STAFF_ACTIVATED,
            actor=request.user,
            entity_type="User",
            entity_id=user.pk,
            request=request,
        )
        return Response(StaffSerializer(user).data)
