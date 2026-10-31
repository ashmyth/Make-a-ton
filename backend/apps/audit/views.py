import uuid

from django.db.models import Q
from django.utils.dateparse import parse_datetime
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from apps.access_control.permissions import IsAdministrator

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Administrator-only, read-only audit trail.

    Filters: ``action``, ``entity_type``, ``entity_id``, ``actor`` (user id),
    ``from`` / ``to`` (ISO 8601 timestamps), ``search`` (actor email or entity id).
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdministrator]

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("actor").order_by("-timestamp")
        params = self.request.query_params
        for param in ("action", "entity_type", "entity_id"):
            if value := params.get(param):
                queryset = queryset.filter(**{param: value})
        if actor := params.get("actor"):
            try:
                actor_id = uuid.UUID(actor)
            except ValueError as exc:
                raise ValidationError({"actor": "Invalid user id."}) from exc
            queryset = queryset.filter(actor_id=actor_id)
        for param, lookup in (("from", "timestamp__gte"), ("to", "timestamp__lte")):
            if raw := params.get(param):
                parsed = parse_datetime(raw)
                if parsed is None:
                    raise ValidationError({param: "Use an ISO 8601 timestamp."})
                queryset = queryset.filter(**{lookup: parsed})
        if search := params.get("search"):
            queryset = queryset.filter(
                Q(actor__email__icontains=search) | Q(entity_id__icontains=search)
            )
        return queryset
