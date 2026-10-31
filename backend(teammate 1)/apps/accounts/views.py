import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.models import AuditAction
from apps.audit.services import record_audit

from .serializers import (
    CsrfSerializer,
    LoginSerializer,
    MessageSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)
from .services import consume_password_reset, issue_password_reset

logger = logging.getLogger(__name__)
User = get_user_model()

INVALID_CREDENTIALS = "Invalid email or password."
RESET_REQUESTED_MESSAGE = (
    "If an account exists for that email, a password reset link has been sent."
)


@method_decorator(csrf_protect, name="dispatch")
class PublicAuthView(APIView):
    """Unauthenticated endpoint with CSRF enforcement (prevents login CSRF) and throttling."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]


class CsrfView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(responses=CsrfSerializer)
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class RegisterView(PublicAuthView):
    throttle_scope = "register"

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserProfileSerializer, 400: OpenApiResponse(description="Validation")},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                user = serializer.save()
                record_audit(
                    action=AuditAction.USER_REGISTERED,
                    actor=user,
                    entity_type="User",
                    entity_id=user.pk,
                    request=request,
                )
        except IntegrityError:
            return Response(
                {"email": ["A user with this email already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(PublicAuthView):
    throttle_scope = "login"

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Invalid credentials"),
            429: OpenApiResponse(description="Account locked or throttled"),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        with transaction.atomic():
            user = User.objects.select_for_update().filter(email=email).first()
            now = timezone.now()

            if user is not None and user.locked_until is not None:
                if user.locked_until > now:
                    record_audit(
                        action=AuditAction.LOGIN_LOCKED,
                        actor=user,
                        entity_type="User",
                        entity_id=user.pk,
                        request=request,
                    )
                    retry_after = max(1, int((user.locked_until - now).total_seconds()))
                    response = Response(
                        {
                            "detail": "Account temporarily locked after repeated failed "
                            "sign-in attempts. Try again later.",
                            "retry_after_seconds": retry_after,
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                    response["Retry-After"] = str(retry_after)
                    return response
                # Lock window elapsed: start counting afresh.
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

            authenticated = authenticate(request, username=email, password=password)
            if authenticated is not None:
                if user.failed_login_attempts or user.locked_until:
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])
                login(request, authenticated)
                record_audit(
                    action=AuditAction.LOGIN_SUCCESS,
                    actor=authenticated,
                    entity_type="User",
                    entity_id=authenticated.pk,
                    request=request,
                )
                return Response(UserProfileSerializer(authenticated).data)

            details = {"email": email[:254]}
            if user is not None:
                user.failed_login_attempts += 1
                details["failed_attempts"] = user.failed_login_attempts
                if user.failed_login_attempts >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
                    user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
                    details["locked_until"] = user.locked_until.isoformat()
                user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])
            record_audit(
                action=AuditAction.LOGIN_FAILED,
                actor=user,
                entity_type="User",
                entity_id=user.pk if user else "",
                details=details,
                request=request,
            )
        return Response({"detail": INVALID_CREDENTIALS}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        record_audit(
            action=AuditAction.LOGOUT,
            actor=request.user,
            entity_type="User",
            entity_id=request.user.pk,
            request=request,
        )
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserProfileSerializer)
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class PasswordResetRequestView(PublicAuthView):
    throttle_scope = "password_reset"

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: MessageSerializer})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issued = issue_password_reset(serializer.validated_data["email"])
        if issued is not None:
            user, _ = issued
            record_audit(
                action=AuditAction.PASSWORD_RESET_REQUESTED,
                actor=user,
                entity_type="User",
                entity_id=user.pk,
                request=request,
            )
        return Response({"detail": RESET_REQUESTED_MESSAGE})


class PasswordResetConfirmView(PublicAuthView):
    throttle_scope = "password_reset_confirm"

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: MessageSerializer, 400: OpenApiResponse(description="Invalid token")},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = consume_password_reset(
            serializer.validated_data["token"], serializer.validated_data["new_password"]
        )
        if user is None:
            return Response(
                {"detail": "This reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record_audit(
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            actor=user,
            entity_type="User",
            entity_id=user.pk,
            request=request,
        )
        return Response({"detail": "Password updated. You can now sign in."})
