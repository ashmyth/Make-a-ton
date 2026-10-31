from rest_framework.permissions import BasePermission
from apps.accounts.models import UserRole


class IsAuthenticatedAndActive(BasePermission):
    """Allows access only to authenticated and active users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsCustomerUser(BasePermission):
    """Allows access only to active Customer portal users."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.role == UserRole.CUSTOMER
        )


class IsFinanceStaff(BasePermission):
    """Allows access to Finance and Administrator staff."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.role in [UserRole.FINANCE, UserRole.ADMINISTRATOR]
        )


class IsStaffUser(BasePermission):
    """Allows access to any internal staff (Admin, Finance, Operations)."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.role in [UserRole.ADMINISTRATOR, UserRole.FINANCE, UserRole.OPERATIONS]
        )


class CustomerDataIsolation(BasePermission):
    """
    Object-level permission that strictly isolates customer data:
    Verifies that obj.customer_id == request.user.customer_id or obj.id == request.user.customer_id.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False

        # Staff can view based on role
        if request.user.role in [UserRole.ADMINISTRATOR, UserRole.FINANCE, UserRole.OPERATIONS]:
            return True

        if request.user.role != UserRole.CUSTOMER:
            return False

        customer_id = request.user.customer_id
        if not customer_id:
            return False

        # If checking a Customer object directly
        if hasattr(obj, "id") and str(obj.id) == str(customer_id):
            return True

        # If checking an object with a customer_id field or customer FK
        obj_cust_id = getattr(obj, "customer_id", None)
        if obj_cust_id and str(obj_cust_id) == str(customer_id):
            return True

        return False
