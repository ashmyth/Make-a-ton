from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.access_control.roles import UserRole

from .models import normalize_email

User = get_user_model()


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
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value: str) -> str:
        return validate_new_password(value)

    def create(self, validated_data):
        return User.objects.create_user(role=UserRole.CUSTOMER, **validated_data)


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


class MessageSerializer(serializers.Serializer):
    detail = serializers.CharField()


class CsrfSerializer(serializers.Serializer):
    csrfToken = serializers.CharField()
