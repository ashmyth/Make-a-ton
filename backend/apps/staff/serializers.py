from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.access_control.roles import ASSIGNABLE_STAFF_ROLE_CHOICES, UserRole
from apps.accounts.serializers import NormalizedEmailField, validate_new_password

User = get_user_model()


class StaffSerializer(serializers.ModelSerializer):
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
            "is_active",
            "last_login",
            "created_at",
        ]
        read_only_fields = fields


class StaffCreateSerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=254)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=ASSIGNABLE_STAFF_ROLE_CHOICES)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value: str) -> str:
        return validate_new_password(value)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class StaffUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    role = serializers.ChoiceField(choices=ASSIGNABLE_STAFF_ROLE_CHOICES, required=False)

    def validate_role(self, value: str) -> str:
        if self.instance is not None and self.instance.role == UserRole.ADMINISTRATOR:
            raise serializers.ValidationError("The role of an administrator cannot be changed.")
        return value

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])
        return instance
