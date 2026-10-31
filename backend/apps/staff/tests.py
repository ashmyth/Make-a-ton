from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.access_control.roles import UserRole
from apps.audit.models import AuditLog, AuditAction

User = get_user_model()
PASSWORD = "StaffPass123!"


class StaffManagementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@brightloop.test",
            password=PASSWORD,
            role=UserRole.ADMINISTRATOR,
        )
        self.ops = User.objects.create_user(
            email="ops@brightloop.test",
            password=PASSWORD,
            role=UserRole.OPERATIONS,
        )

    def test_admin_creates_staff(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post("/api/v1/staff/", {
            "email": "finance_new@brightloop.test",
            "password": "SecureFinance123!",
            "first_name": "Frank",
            "last_name": "Finance",
            "role": UserRole.FINANCE,
        })
        self.assertEqual(res.status_code, 201)
        created_user = User.objects.get(email="finance_new@brightloop.test")
        self.assertEqual(created_user.role, UserRole.FINANCE)
        self.assertTrue(created_user.is_active)

        # Audit entry
        log = AuditLog.objects.filter(action=AuditAction.STAFF_CREATED, entity_id=str(created_user.pk)).first()
        self.assertIsNotNone(log)

    def test_non_admin_cannot_create_staff(self):
        self.client.force_authenticate(user=self.ops)
        res = self.client.post("/api/v1/staff/", {
            "email": "intruder@brightloop.test",
            "password": "SecureFinance123!",
            "first_name": "Hacker",
            "last_name": "User",
            "role": UserRole.OPERATIONS,
        })
        self.assertEqual(res.status_code, 403)

    def test_soft_deactivation(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(f"/api/v1/staff/{self.ops.pk}/deactivate/")
        self.assertEqual(res.status_code, 200)

        self.ops.refresh_from_db()
        self.assertFalse(self.ops.is_active)

        # Deactivated user cannot log in
        login_res = self.client.post("/api/v1/auth/login/", {
            "email": "ops@brightloop.test",
            "password": PASSWORD,
        })
        self.assertEqual(login_res.status_code, 403)

    def test_cannot_deactivate_self(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(f"/api/v1/staff/{self.admin.pk}/deactivate/")
        self.assertEqual(res.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

