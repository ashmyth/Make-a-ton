from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.access_control.roles import UserRole

from .models import Customer

User = get_user_model()

# Fields a customer may edit on their own record (contact + address).
CUSTOMER_EDITABLE_FIELDS = frozenset(
    {
        "contact_person",
        "email",
        "phone",
        "billing_street",
        "billing_city",
        "billing_state",
        "billing_postal_code",
        "billing_country",
    }
)


class CustomerSerializer(serializers.ModelSerializer):
    portal_user_id = serializers.UUIDField(read_only=True, allow_null=True)
    portal_user_email = serializers.EmailField(
        source="portal_user.email", read_only=True, default=None
    )

    class Meta:
        model = Customer
        fields = [
            "id",
            "customer_code",
            "customer_type",
            "display_name",
            "contact_person",
            "email",
            "phone",
            "billing_street",
            "billing_city",
            "billing_state",
            "billing_postal_code",
            "billing_country",
            "tax_identifier",
            "payment_terms",
            "status",
            "portal_user_id",
            "portal_user_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_code",
            "status",
            "portal_user_id",
            "portal_user_email",
            "created_at",
            "updated_at",
        ]

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate_display_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value


class LinkPortalUserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()

    def validate_user_id(self, value):
        user = User.objects.filter(pk=value).first()
        if user is None:
            raise serializers.ValidationError("User not found.")
        if user.role != UserRole.CUSTOMER:
            raise serializers.ValidationError("Only customer portal users can be linked.")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")
        if Customer.objects.filter(portal_user=user).exists():
            raise serializers.ValidationError("User is already linked to a customer.")
        self.context["portal_user"] = user
        return value
