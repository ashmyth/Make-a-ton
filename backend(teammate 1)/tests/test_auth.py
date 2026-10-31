import re
from datetime import timedelta

import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import PasswordResetToken, User
from apps.accounts.services import hash_token
from apps.accounts.validators import BrightloopPasswordValidator
from apps.audit.models import AuditAction, AuditLog
from tests.factories import PASSWORD, UserFactory

LOGIN = "/api/v1/auth/login/"
REGISTER = "/api/v1/auth/register/"
RESET = "/api/v1/auth/password-reset/"
CONFIRM = "/api/v1/auth/password-reset-confirm/"
NEW_PASSWORD = "N3w!Passw0rd"


def login(client, email, password=PASSWORD):
    return client.post(LOGIN, {"email": email, "password": password}, format="json")


class TestPasswordValidation:
    validator = BrightloopPasswordValidator()

    @pytest.mark.parametrize(
        "password,code",
        [
            ("Ab1!xyz", "password_too_short"),
            ("lowercase!1x", "password_no_upper"),
            ("UPPERCASE!1X", "password_no_lower"),
            ("NoSpecial123x", "password_no_special"),
        ],
    )
    def test_invalid_passwords(self, password, code):
        with pytest.raises(ValidationError) as exc:
            self.validator.validate(password)
        assert code in [e.code for e in exc.value.error_list]

    def test_nine_characters_is_accepted(self):
        self.validator.validate("Abcdef!gh")

    def test_eight_characters_is_rejected(self):
        with pytest.raises(ValidationError):
            self.validator.validate("Abcde!gh")

    def test_valid_password(self):
        self.validator.validate(PASSWORD)


@pytest.mark.django_db
class TestRegistration:
    payload = {
        "email": "  Alice@Example.COM ",
        "password": PASSWORD,
        "first_name": "Alice",
        "last_name": "Anderson",
    }

    def test_register_creates_customer_role_user_with_argon2id(self, api):
        response = api.post(REGISTER, self.payload, format="json")
        assert response.status_code == 201
        assert response.data["email"] == "alice@example.com"
        assert response.data["role"] == "CUSTOMER"
        assert response.data["customer_id"] is None
        assert "password" not in response.data
        user = User.objects.get(email="alice@example.com")
        assert user.password.startswith("argon2$argon2id$")
        assert AuditLog.objects.filter(action=AuditAction.USER_REGISTERED, actor=user).exists()

    def test_duplicate_email_is_rejected_case_insensitively(self, api):
        UserFactory(email="bob@example.com")
        response = api.post(REGISTER, {**self.payload, "email": "BOB@Example.com"}, format="json")
        assert response.status_code == 400
        assert "email" in response.data
        assert User.objects.filter(email="bob@example.com").count() == 1

    def test_weak_password_is_rejected(self, api):
        response = api.post(REGISTER, {**self.payload, "password": "weak"}, format="json")
        assert response.status_code == 400
        assert "password" in response.data
        assert not User.objects.filter(email="alice@example.com").exists()

    def test_missing_fields_are_rejected(self, api):
        response = api.post(REGISTER, {"email": "x@example.com"}, format="json")
        assert response.status_code == 400
        assert {"password", "first_name", "last_name"} <= set(response.data)

    def test_database_enforces_case_insensitive_unique_email(self):
        from django.db import IntegrityError, transaction

        UserFactory(email="dup@example.com")
        with pytest.raises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="DUP@example.com", password="x")])


@pytest.mark.django_db
class TestLoginSessionAndCsrf:
    def test_login_me_logout_cycle(self, api):
        user = UserFactory(email="carol@example.com")
        response = login(api, "Carol@Example.com")
        assert response.status_code == 200
        assert response.data["id"] == str(user.pk)
        assert response.cookies["sessionid"]["httponly"]

        me = api.get("/api/v1/auth/me/")
        assert me.status_code == 200
        assert me.data["email"] == "carol@example.com"
        assert me.data["customer_id"] is None

        assert api.post("/api/v1/auth/logout/").status_code == 204
        assert api.get("/api/v1/auth/me/").status_code == 403
        actions = set(AuditLog.objects.filter(actor=user).values_list("action", flat=True))
        assert {AuditAction.LOGIN_SUCCESS, AuditAction.LOGOUT} <= actions

    def test_me_returns_customer_id_for_linked_portal_user(self, make_client, customer_user):
        response = make_client(customer_user).get("/api/v1/auth/me/")
        assert response.data["customer_id"] == str(customer_user.customer.pk)
        assert response.data["role"] == "CUSTOMER"

    def test_me_requires_authentication(self, api):
        assert api.get("/api/v1/auth/me/").status_code == 403

    def test_login_failure_is_neutral_for_unknown_and_known_accounts(self, api):
        UserFactory(email="dave@example.com")
        known = login(api, "dave@example.com", "Wrong!Passw0rd")
        unknown = login(api, "nobody@example.com", "Wrong!Passw0rd")
        assert known.status_code == unknown.status_code == 401
        assert known.data == unknown.data

    def test_failed_login_is_audited(self, api):
        login(api, "nobody@example.com", "Wrong!Passw0rd")
        log = AuditLog.objects.get(action=AuditAction.LOGIN_FAILED)
        assert log.actor is None
        assert log.details["email"] == "nobody@example.com"
        assert log.ip_address == "127.0.0.1"

    def test_csrf_endpoint_sets_cookie(self, api):
        response = api.get("/api/v1/auth/csrf/")
        assert response.status_code == 200
        assert response.data["csrfToken"]
        assert "csrftoken" in response.cookies

    def test_login_requires_csrf_token_when_enforced(self):
        UserFactory(email="erin@example.com")
        client = APIClient(enforce_csrf_checks=True)
        assert login(client, "erin@example.com").status_code == 403
        token = client.get("/api/v1/auth/csrf/").data["csrfToken"]
        response = client.post(
            LOGIN,
            {"email": "erin@example.com", "password": PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        assert response.status_code == 200

    def test_authenticated_post_requires_csrf_token(self):
        UserFactory(email="frank@example.com")
        client = APIClient(enforce_csrf_checks=True)
        token = client.get("/api/v1/auth/csrf/").data["csrfToken"]
        client.post(
            LOGIN,
            {"email": "frank@example.com", "password": PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        assert client.post("/api/v1/auth/logout/").status_code == 403

    def test_inactive_user_cannot_login(self, api):
        UserFactory(email="gone@example.com", is_active=False)
        assert login(api, "gone@example.com").status_code == 401


@pytest.mark.django_db
class TestLockoutAndThrottling:
    def test_account_locks_for_15_minutes_after_5_failures(self, api):
        user = UserFactory(email="heidi@example.com")
        for attempt in range(5):
            assert login(api, "heidi@example.com", "Wrong!Passw0rd").status_code == 401, attempt
        user.refresh_from_db()
        assert user.failed_login_attempts == 5
        remaining = user.locked_until - timezone.now()
        assert timedelta(minutes=14) < remaining <= timedelta(minutes=15)

        # Correct password is still refused while locked.
        locked = login(api, "heidi@example.com")
        assert locked.status_code == 429
        assert locked["Retry-After"]
        assert AuditLog.objects.filter(action=AuditAction.LOGIN_LOCKED, actor=user).exists()
        assert api.get("/api/v1/auth/me/").status_code == 403

    def test_four_failures_do_not_lock(self, api):
        user = UserFactory(email="ivan@example.com")
        for _ in range(4):
            login(api, "ivan@example.com", "Wrong!Passw0rd")
        user.refresh_from_db()
        assert user.locked_until is None
        assert login(api, "ivan@example.com").status_code == 200

    def test_successful_login_resets_failure_counter(self, api):
        user = UserFactory(email="judy@example.com")
        for _ in range(3):
            login(api, "judy@example.com", "Wrong!Passw0rd")
        assert login(api, "judy@example.com").status_code == 200
        user.refresh_from_db()
        assert user.failed_login_attempts == 0

    def test_login_works_after_lock_expires_and_counter_restarts(self, api):
        user = UserFactory(email="ken@example.com")
        User.objects.filter(pk=user.pk).update(
            failed_login_attempts=5, locked_until=timezone.now() - timedelta(seconds=1)
        )
        assert login(api, "ken@example.com", "Wrong!Passw0rd").status_code == 401
        user.refresh_from_db()
        assert user.failed_login_attempts == 1
        assert user.locked_until is None
        assert login(api, "ken@example.com").status_code == 200

    def test_request_throttling_per_client(self, api, monkeypatch):
        monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "login", "3/min")
        for _ in range(3):
            assert login(api, "nobody@example.com", "Wrong!Passw0rd").status_code == 401
        throttled = login(api, "nobody@example.com", "Wrong!Passw0rd")
        assert throttled.status_code == 429
        assert "throttled" in throttled.data["detail"].lower()


def _token_from_outbox(index=-1):
    return re.search(r"token=([\w-]+)", mail.outbox[index].body).group(1)


@pytest.mark.django_db
class TestPasswordResetFlow:
    def test_neutral_response_for_unknown_and_known_email(self, api):
        UserFactory(email="lena@example.com")
        known = api.post(RESET, {"email": "lena@example.com"}, format="json")
        unknown = api.post(RESET, {"email": "ghost@example.com"}, format="json")
        assert known.status_code == unknown.status_code == 200
        assert known.data == unknown.data
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["lena@example.com"]
        assert PasswordResetToken.objects.count() == 1

    def test_inactive_account_gets_no_email(self, api):
        UserFactory(email="off@example.com", is_active=False)
        assert api.post(RESET, {"email": "off@example.com"}, format="json").status_code == 200
        assert mail.outbox == []

    def test_only_hash_is_stored_and_link_points_to_frontend(self, api):
        UserFactory(email="mona@example.com")
        api.post(RESET, {"email": "mona@example.com"}, format="json")
        token = _token_from_outbox()
        row = PasswordResetToken.objects.get()
        assert row.token_hash == hash_token(token)
        assert token not in row.token_hash
        assert "https://app.example.test/reset-password?token=" in mail.outbox[0].body
        window = row.expires_at - row.created_at
        assert timedelta(minutes=29) < window <= timedelta(minutes=30, seconds=5)

    def test_token_is_single_use_and_sets_new_password(self, api):
        user = UserFactory(email="nick@example.com")
        api.post(RESET, {"email": "nick@example.com"}, format="json")
        token = _token_from_outbox()

        ok = api.post(CONFIRM, {"token": token, "new_password": NEW_PASSWORD}, format="json")
        assert ok.status_code == 200
        again = api.post(
            CONFIRM, {"token": token, "new_password": "An0ther!Passw0rd"}, format="json"
        )
        assert again.status_code == 400

        assert login(api, "nick@example.com").status_code == 401
        assert login(api, "nick@example.com", NEW_PASSWORD).status_code == 200
        actions = set(AuditLog.objects.filter(actor=user).values_list("action", flat=True))
        assert {
            AuditAction.PASSWORD_RESET_REQUESTED,
            AuditAction.PASSWORD_RESET_COMPLETED,
        } <= actions

    def test_expired_token_is_rejected(self, api):
        UserFactory(email="olga@example.com")
        api.post(RESET, {"email": "olga@example.com"}, format="json")
        PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = api.post(
            CONFIRM, {"token": _token_from_outbox(), "new_password": NEW_PASSWORD}, format="json"
        )
        assert response.status_code == 400

    def test_unknown_token_is_rejected(self, api):
        response = api.post(
            CONFIRM, {"token": "not-a-real-token", "new_password": NEW_PASSWORD}, format="json"
        )
        assert response.status_code == 400

    def test_weak_new_password_is_rejected_and_token_survives(self, api):
        UserFactory(email="pia@example.com")
        api.post(RESET, {"email": "pia@example.com"}, format="json")
        token = _token_from_outbox()
        weak = api.post(CONFIRM, {"token": token, "new_password": "short"}, format="json")
        assert weak.status_code == 400
        assert "new_password" in weak.data
        ok = api.post(CONFIRM, {"token": token, "new_password": NEW_PASSWORD}, format="json")
        assert ok.status_code == 200

    def test_new_request_invalidates_previous_token(self, api):
        UserFactory(email="quinn@example.com")
        api.post(RESET, {"email": "quinn@example.com"}, format="json")
        api.post(RESET, {"email": "quinn@example.com"}, format="json")
        old, new = _token_from_outbox(0), _token_from_outbox(1)
        assert (
            api.post(
                CONFIRM, {"token": old, "new_password": NEW_PASSWORD}, format="json"
            ).status_code
            == 400
        )
        assert (
            api.post(
                CONFIRM, {"token": new, "new_password": NEW_PASSWORD}, format="json"
            ).status_code
            == 200
        )

    def test_reset_clears_lockout_and_ends_existing_sessions(self, api, make_client):
        user = UserFactory(email="ruth@example.com")
        logged_in = make_client(user)
        assert logged_in.get("/api/v1/auth/me/").status_code == 200
        User.objects.filter(pk=user.pk).update(
            failed_login_attempts=5, locked_until=timezone.now() + timedelta(minutes=10)
        )
        api.post(RESET, {"email": "ruth@example.com"}, format="json")
        api.post(
            CONFIRM, {"token": _token_from_outbox(), "new_password": NEW_PASSWORD}, format="json"
        )
        user.refresh_from_db()
        assert user.failed_login_attempts == 0 and user.locked_until is None
        assert logged_in.get("/api/v1/auth/me/").status_code == 403
        assert login(api, "ruth@example.com", NEW_PASSWORD).status_code == 200

    def test_email_failure_still_returns_neutral_response(self, api, settings):
        settings.EMAIL_BACKEND = "tests.test_auth.BrokenEmailBackend"
        UserFactory(email="sam@example.com")
        response = api.post(RESET, {"email": "sam@example.com"}, format="json")
        assert response.status_code == 200


from django.core.mail.backends.base import BaseEmailBackend  # noqa: E402


class BrokenEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise ConnectionError("smtp down")
