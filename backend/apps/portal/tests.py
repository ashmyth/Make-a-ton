from decimal import Decimal
import uuid
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRole
from apps.customers.models import Customer
from apps.subscriptions.models import Subscription, SubscriptionStatus
from apps.billing.models import Invoice, InvoiceStatus
from apps.portal.models import CustomerRequest, RequestType


class CustomerPortalTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Customer A
        self.user_a = User.objects.create_user(
            email="cust_a@alpha.com",
            password="SecurePassword@123",
            role=UserRole.CUSTOMER,
            first_name="Alpha",
            last_name="User",
        )
        self.customer_a = Customer.objects.create(
            customer_code="CUST-AAA",
            display_name="Alpha Tech",
            contact_person="Alice",
            email="cust_a@alpha.com",
            phone="111-222-3333",
            billing_street="1 Alpha Way",
            billing_city="Bengaluru",
            billing_state="KA",
            billing_postal_code="560001",
            billing_country="India",
            portal_user=self.user_a,
        )

        # Customer B
        self.user_b = User.objects.create_user(
            email="cust_b@beta.com",
            password="SecurePassword@123",
            role=UserRole.CUSTOMER,
            first_name="Beta",
            last_name="User",
        )
        self.customer_b = Customer.objects.create(
            customer_code="CUST-BBB",
            display_name="Beta Solutions",
            contact_person="Bob",
            email="cust_b@beta.com",
            phone="444-555-6666",
            billing_street="2 Beta Rd",
            billing_city="Mumbai",
            billing_state="MH",
            billing_postal_code="400001",
            billing_country="India",
            portal_user=self.user_b,
        )

        today = timezone.now().date()
        self.sub_a = Subscription.objects.create(
            subscription_number="SUB-A-01",
            customer=self.customer_a,
            plan_name="Enterprise Cloud",
            start_date=today,
            status=SubscriptionStatus.ACTIVE,
        )
        self.inv_a = Invoice.objects.create(
            invoice_number="INV-A-101",
            customer=self.customer_a,
            subscription=self.sub_a,
            issue_date=today,
            due_date=today + timezone.timedelta(days=30),
            subtotal=Decimal("5000.00"),
            total_amount=Decimal("5000.00"),
            outstanding_balance=Decimal("5000.00"),
            currency="INR",
            status=InvoiceStatus.CONFIRMED,
        )

        self.sub_b = Subscription.objects.create(
            subscription_number="SUB-B-01",
            customer=self.customer_b,
            plan_name="Starter Tier",
            start_date=today,
            status=SubscriptionStatus.ACTIVE,
        )
        self.inv_b = Invoice.objects.create(
            invoice_number="INV-B-201",
            customer=self.customer_b,
            subscription=self.sub_b,
            issue_date=today,
            due_date=today + timezone.timedelta(days=30),
            subtotal=Decimal("2000.00"),
            total_amount=Decimal("2000.00"),
            outstanding_balance=Decimal("2000.00"),
            currency="INR",
            status=InvoiceStatus.CONFIRMED,
        )

    def test_customer_portal_data_isolation(self):
        """Customer A querying invoices or subscriptions must NEVER see Customer B's records."""
        self.client.force_authenticate(user=self.user_a)

        # Invoices
        resp = self.client.get("/api/v1/portal/invoices/")
        self.assertEqual(resp.status_code, 200)
        invoice_numbers = [item["invoice_number"] for item in resp.data]
        self.assertIn("INV-A-101", invoice_numbers)
        self.assertNotIn("INV-B-201", invoice_numbers)

        # Subscriptions
        resp = self.client.get("/api/v1/portal/subscriptions/")
        self.assertEqual(resp.status_code, 200)
        sub_numbers = [item["subscription_number"] for item in resp.data]
        self.assertIn("SUB-A-01", sub_numbers)
        self.assertNotIn("SUB-B-01", sub_numbers)

    def test_idor_protection_single_invoice_access(self):
        """Customer A trying to directly fetch Customer B's invoice by ID must be blocked."""
        self.client.force_authenticate(user=self.user_a)

        # Customer A accessing Customer B's invoice
        resp = self.client.get(f"/api/v1/portal/invoices/{self.inv_b.id}/")
        self.assertIn(resp.status_code, [403, 404])

        # Customer A accessing Customer B's invoice download
        resp_dl = self.client.get(f"/api/v1/portal/invoices/{self.inv_b.id}/download/")
        self.assertEqual(resp_dl.status_code, 403)

    def test_permitted_profile_updates(self):
        """Customer can update contact and phone, but not financial or status fields (PRD §4.2)."""
        self.client.force_authenticate(user=self.user_a)

        resp = self.client.patch("/api/v1/portal/profile/", {
            "phone": "+919999999999",
            "contact_person": "Alice Updated",
            "status": "ARCHIVED",  # forbidden attempt
            "payment_terms": "IMMEDIATE",  # forbidden attempt
        })
        self.assertEqual(resp.status_code, 200)
        self.customer_a.refresh_from_db()
        self.assertEqual(self.customer_a.phone, "+919999999999")
        self.assertEqual(self.customer_a.contact_person, "Alice Updated")
        self.assertEqual(self.customer_a.status, "ACTIVE")  # untouched
        self.assertEqual(self.customer_a.payment_terms, "NET_30")  # untouched

    def test_self_service_lifecycle_request_submission(self):
        """Customer can submit pause/cancel/renew requests."""
        self.client.force_authenticate(user=self.user_a)

        resp = self.client.post("/api/v1/portal/requests/", {
            "subscription": str(self.sub_a.id),
            "request_type": "pause",
            "notes": "Please pause subscription during holiday break.",
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(CustomerRequest.objects.filter(customer=self.customer_a).count(), 1)
        req_obj = CustomerRequest.objects.first()
        self.assertEqual(req_obj.request_type, "pause")
        self.assertEqual(req_obj.status, "submitted")
