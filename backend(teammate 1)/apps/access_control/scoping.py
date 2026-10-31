"""Queryset scoping helper for customer data isolation."""

from django.db.models import QuerySet

from .roles import STAFF_ROLES, UserRole


def scope_to_customer(queryset: QuerySet, user, field: str = "customer_id") -> QuerySet:
    """Staff see everything. Customers only see rows whose ``field`` is their customer.

    Anyone else, or a customer without a linked record, gets an empty queryset.
    """
    if user.role in STAFF_ROLES:
        return queryset
    if user.role == UserRole.CUSTOMER and user.customer_id is not None:
        return queryset.filter(**{field: user.customer_id})
    return queryset.none()
