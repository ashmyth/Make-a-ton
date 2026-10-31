from django.db import models


class UserRole(models.TextChoices):
    ADMINISTRATOR = "ADMINISTRATOR", "Administrator"
    OPERATIONS = "OPERATIONS", "Operations Staff"
    FINANCE = "FINANCE", "Finance Staff"
    CUSTOMER = "CUSTOMER", "Customer"


STAFF_ROLES = frozenset({UserRole.ADMINISTRATOR, UserRole.OPERATIONS, UserRole.FINANCE})
# Roles an administrator may assign through the staff API.
ASSIGNABLE_STAFF_ROLES = (UserRole.OPERATIONS, UserRole.FINANCE)
ASSIGNABLE_STAFF_ROLE_CHOICES = [(role.value, role.label) for role in ASSIGNABLE_STAFF_ROLES]
