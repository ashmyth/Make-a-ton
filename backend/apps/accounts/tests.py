from datetime import timedelta
from django.test import TestCase
from django.core import mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, PasswordResetToken
from apps.accounts.validators import BrightloopPasswordValidator
from apps.access_control.roles import UserRole
from apps.audit.models import AuditLog, AuditAction

PASSWORD = "ValidPass123!"


class PasswordValidationTestCase(TestCase):
    def setUp(self):
        self.validator = BrightloopPasswordValidator()

    def test_invalid_passwords(self):
        with self.assertRaises(ValidationError):
            self.validator.validate("Ab1!xyz")  # too short
        with self.assertRaises(ValidationError):
            self.validator.validate("lowercase!1x")  # no upper
        with self.assertRaises(ValidationError):
            self.validator.validate("UPPERCASE!1X")  # no lower
        with self.assertRaises(ValidationError):
            self.validator.validate("NoSpecial123x")  # no special

    def test_valid_passwords(self):
        self.validator.validate("Abcdef!gh")
        self.validator.validate(PASSWORD)


class AccountsAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@brightloop.test",
            password=PASSWORD,
            role=UserRole.CUSTOMER,
        )

    def test_registration(self):
        res = self.client.post("/api/v1/auth/register/", {
            "email": "  NewUser@BrightLoop.Test ",
            "password": "SecurePassword123!",
            "first_name": "New",
            "last_name": "User",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["email"], "newuser@brightloop.test")
        new_user = User.objects.get(email="newuser@brightloop.test")
        self.assertEqual(new_user.role, UserRole.CUSTOMER)

        # Audit check
        log = AuditLog.objects.filter(action=AuditAction.USER_REGISTERED, entity_id=str(new_user.pk)).first()
        self.assertIsNotNone(log)

    def test_login_success(self):
        res = self.client.post("/api/v1/auth/login/", {
            "email": "testuser@brightloop.test",
            "password": PASSWORD,
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["email"], "testuser@brightloop.test")

        log = AuditLog.objects.filter(action=AuditAction.LOGIN_SUCCESS, actor=self.user).first()
        self.assertIsNotNone(log)

    def test_login_failed_and_lockout(self):
        # 4 failed attempts
        for i in range(1, 5):
            res = self.client.post("/api/v1/auth/login/", {
                "email": "testuser@brightloop.test",
                "password": "WrongPassword!",
            })
            self.assertEqual(res.status_code, 401)
            self.user.refresh_from_db()
            self.assertEqual(self.user.failed_login_attempts, i)
            self.assertIsNone(self.user.locked_until)

        # 5th attempt locks account
        res = self.client.post("/api/v1/auth/login/", {
            "email": "testuser@brightloop.test",
            "password": "WrongPassword!",
        })
        self.assertEqual(res.status_code, 401)
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 5)
        self.assertIsNotNone(self.user.locked_until)

        # 6th attempt returns 429 Too Many Requests
        res_locked = self.client.post("/api/v1/auth/login/", {
            "email": "testuser@brightloop.test",
            "password": PASSWORD,  # even with correct password
        })
        self.assertEqual(res_locked.status_code, 429)
        self.assertIn("Retry-After", res_locked.headers)

    def test_password_reset_flow(self):
        # 1. Request reset
        res_req = self.client.post("/api/v1/auth/password-reset/", {
            "email": "testuser@brightloop.test",
        })
        self.assertEqual(res_req.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        self.assertIn("reset-password?token=", email_body)

        token = email_body.split("token=")[1].split()[0].strip()

        # 2. Confirm reset
        new_pass = "BrandNewSecret123!"
        res_confirm = self.client.post("/api/v1/auth/password-reset/confirm/", {
            "token": token,
            "new_password": new_pass,
        })
        self.assertEqual(res_confirm.status_code, 200)

        # 3. Verify sign in with new password
        res_login = self.client.post("/api/v1/auth/login/", {
            "email": "testuser@brightloop.test",
            "password": new_pass,
        })
        self.assertEqual(res_login.status_code, 200)
