from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.access_control.roles import UserRole
from apps.customers.models import Customer, CustomerStatus
from apps.audit.models import AuditLog, AuditAction

User = get_user_model()
PASSWORD = "CustomerPass123!"


class CustomerCRMTestCase(TestCase):
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
        self.portal_user_a = User.objects.create_user(
            email="alice@brightloop.test",
            password=PASSWORD,
            role=UserRole.CUSTOMER,
        )
        self.portal_user_b = User.objects.create_user(
            email="bob@brightloop.test",
            password=PASSWORD,
            role=UserRole.CUSTOMER,
        )
        self.customer_a = Customer.objects.create_with_code(
            display_name="Alice Enterprise",
            email="alice@brightloop.test",
            contact_person="Alice",
            billing_street="100 Main St",
            billing_city="Bengaluru",
            billing_country="India",
            portal_user=self.portal_user_a,
        )
        self.customer_b = Customer.objects.create_with_code(
            display_name="Bob Logistics",
            email="bob@brightloop.test",
            contact_person="Bob",
            billing_street="200 Sea Road",
            billing_city="Mumbai",
            billing_country="India",
            portal_user=self.portal_user_b,
        )

    def test_create_customer(self):
        self.client.force_authenticate(user=self.ops)
        res = self.client.post("/api/v1/customers/", {
            "display_name": "New Client Ltd",
            "email": "contact@newclient.test",
            "contact_person": "Charles",
            "billing_street": "300 Tech Park",
            "billing_city": "Hyderabad",
            "billing_country": "India",
            "customer_type": "BUSINESS",
        })
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["customer_code"].startswith("CUST-"))

    def test_customer_data_isolation(self):
        self.client.force_authenticate(user=self.portal_user_a)
        # Attempt to access customer B
        res = self.client.get(f"/api/v1/customers/{self.customer_b.pk}/")
        self.assertEqual(res.status_code, 403)

        # Access self
        res_self = self.client.get(f"/api/v1/customers/{self.customer_a.pk}/")
        self.assertEqual(res_self.status_code, 200)

    def test_customer_field_editing_boundaries(self):
        self.client.force_authenticate(user=self.portal_user_a)
        # Cannot modify payment_terms
        res_forbidden = self.client.patch(f"/api/v1/customers/{self.customer_a.pk}/", {
            "payment_terms": "IMMEDIATE",
        })
        self.assertEqual(res_forbidden.status_code, 403)

        # Permitted update
        res_ok = self.client.patch(f"/api/v1/customers/{self.customer_a.pk}/", {
            "contact_person": "Alice Smith",
        })
        self.assertEqual(res_ok.status_code, 200)
        self.customer_a.refresh_from_db()
        self.assertEqual(self.customer_a.contact_person, "Alice Smith")

    def test_soft_archiving(self):
        self.client.force_authenticate(user=self.ops)
        res = self.client.post(f"/api/v1/customers/{self.customer_a.pk}/archive/")
        self.assertEqual(res.status_code, 200)
        self.customer_a.refresh_from_db()
        self.assertEqual(self.customer_a.status, CustomerStatus.ARCHIVED)
