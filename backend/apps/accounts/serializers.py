from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.access_control.roles import UserRole

User = get_user_model()


def normalize_email(email: str) -> str:
    return email.strip().lower()


class NormalizedEmailField(serializers.EmailField):
    def to_internal_value(self, data):
        return normalize_email(super().to_internal_value(data))


def validate_new_password(value: str) -> str:
    try:
        validate_password(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return value


class UserProfileSerializer(serializers.ModelSerializer):
    customer_id = serializers.UUIDField(read_only=True, allow_null=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "customer_id",
            "is_active",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    first_name = serializers.CharField(max_length=150, required=False, default="", allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, default="", allow_blank=True)
    full_name = serializers.CharField(max_length=300, required=False, allow_blank=True)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value: str) -> str:
        return validate_new_password(value)

    def validate(self, attrs):
        full_name = attrs.pop("full_name", "").strip()
        if full_name:
            parts = full_name.split(" ", 1)
            if not attrs.get("first_name"):
                attrs["first_name"] = parts[0]
            if not attrs.get("last_name") and len(parts) > 1:
                attrs["last_name"] = parts[1]
        if not attrs.get("first_name"):
            attrs["first_name"] = attrs.get("email", "").split("@")[0]
        if not attrs.get("last_name"):
            attrs["last_name"] = ""
        return attrs

    def create(self, validated_data):
        company_name = validated_data.pop("company_name", "")
        phone = validated_data.pop("phone", "")
        user = User.objects.create_user(role=UserRole.CUSTOMER, **validated_data)
        from apps.customers.models import Customer, CustomerType
        if not hasattr(user, "customer_profile") or user.customer_profile is None:
            c_name = company_name or f"{user.first_name} {user.last_name}".strip() or user.email
            c_code = f"CUST-{user.pk.hex[:6].upper()}"
            Customer.objects.create(
                portal_user=user,
                customer_code=c_code,
                customer_type=CustomerType.BUSINESS if company_name else CustomerType.INDIVIDUAL,
                display_name=c_name,
                email=user.email,
                phone=phone
            )
        return user


class LoginSerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=254)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate_new_password(self, value: str) -> str:
        return validate_new_password(value)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value: str) -> str:
        return validate_new_password(value)

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user


class MessageSerializer(serializers.Serializer):
    detail = serializers.CharField()


class CsrfSerializer(serializers.Serializer):
    csrfToken = serializers.CharField()
