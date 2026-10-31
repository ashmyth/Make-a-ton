"""Reusable DRF permission classes shared by every Brightloop module.

Administrators are a superset of Operations and Finance for commercial and
financial workflows. Customers are restricted to records they own.
"""

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .roles import STAFF_ROLES, UserRole


def _is_active_user(request: Request) -> bool:
    user = request.user
    return bool(user and user.is_authenticated and user.is_active)


class _RolePermission(BasePermission):
    allowed_roles: frozenset[str] = frozenset()

    def has_permission(self, request: Request, view: APIView) -> bool:
        return _is_active_user(request) and request.user.role in self.allowed_roles


class IsAdministrator(_RolePermission):
    allowed_roles = frozenset({UserRole.ADMINISTRATOR})


class IsOperationsStaff(_RolePermission):
    allowed_roles = frozenset({UserRole.ADMINISTRATOR, UserRole.OPERATIONS})


class IsFinanceStaff(_RolePermission):
    allowed_roles = frozenset({UserRole.ADMINISTRATOR, UserRole.FINANCE})


class IsStaffUser(_RolePermission):
    """Any internal staff role (Administrator, Operations, Finance)."""

    allowed_roles = STAFF_ROLES


class IsCustomerUser(_RolePermission):
    """Customer portal boundary."""

    allowed_roles = frozenset({UserRole.CUSTOMER})


def owning_customer_id(obj: Any) -> Any:
    """Customer id that owns ``obj``.

    A model exposes ownership with an ``owning_customer_id`` property, or with a
    plain ``customer_id`` attribute / foreign key.
    """
    if hasattr(obj, "owning_customer_id"):
        return obj.owning_customer_id
    return getattr(obj, "customer_id", None)


class CustomerDataIsolation(BasePermission):
    """Anti-IDOR guard. Staff pass; customers only reach their own records."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return _is_active_user(request)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        user = request.user
        if user.role in STAFF_ROLES:
            return True
        if user.role != UserRole.CUSTOMER:
            return False
        own_id = user.customer_id
        return own_id is not None and owning_customer_id(obj) == own_id
