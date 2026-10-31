import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditAction
from apps.audit.services import record_audit

from .serializers import (
    ChangePasswordSerializer,
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


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    """Dedicated endpoint to obtain/refresh the CSRF cookie."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request), "detail": "CSRF cookie set."})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CurrentUserView(APIView):
    """Returns authenticated user details matching Teammate 1 contract."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginView(APIView):
    """
    Session login with account lockout (PRD §7.1 / AUTH-02 / AUTH-03):
    Locks account for 15 minutes after 5 consecutive failed attempts.
    Records LOGIN_SUCCESS, LOGIN_FAILED, and LOGIN_LOCKED in the append-only audit trail.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        with transaction.atomic():
            user = User.objects.select_for_update().filter(email=email).first()
            now = timezone.now()

            # Check lockout state
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
                            "detail": "Account temporarily locked after repeated failed sign-in attempts. Try again later.",
                            "retry_after_seconds": retry_after,
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                    response["Retry-After"] = str(retry_after)
                    return response

                # Lock window elapsed: reset counter
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

            if user is not None and not user.is_active and user.check_password(password):
                return Response(
                    {"detail": "Account deactivated. Please contact an administrator."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            authenticated = authenticate(request, email=email, password=password)
            if authenticated is None:
                authenticated = authenticate(request, username=email, password=password)

            if authenticated is not None:
                if not authenticated.is_active:
                    return Response({"detail": "Account deactivated."}, status=status.HTTP_403_FORBIDDEN)

                if user and (user.failed_login_attempts or user.locked_until):
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

            # Record failed attempt and evaluate lockout threshold
            details = {"email": email[:254]}
            if user is not None:
                user.failed_login_attempts += 1
                details["failed_attempts"] = user.failed_login_attempts
                max_attempts = getattr(settings, "LOGIN_MAX_FAILED_ATTEMPTS", 5)
                lockout_mins = getattr(settings, "LOGIN_LOCKOUT_MINUTES", 15)
                if user.failed_login_attempts >= max_attempts:
                    user.locked_until = now + timedelta(minutes=lockout_mins)
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
    """Session logout with audit log recording."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        record_audit(
            action=AuditAction.LOGOUT,
            actor=request.user,
            entity_type="User",
            entity_id=request.user.pk,
            request=request,
        )
        logout(request)
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """Customer self-service registration (PRD §7.1)."""
    permission_classes = [permissions.AllowAny]

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


class PasswordResetRequestView(APIView):
    """Request a password reset link (neutral response prevents user enumeration)."""
    permission_classes = [permissions.AllowAny]

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


class PasswordResetConfirmView(APIView):
    """Confirm a password reset using an unexpired, single-use token."""
    permission_classes = [permissions.AllowAny]

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


class ChangePasswordView(APIView):
    """Authenticated password update."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."})
