from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from sales.models import Customer, Product, Variant, Plan, Order, OrderLine, Payment
from register.models import RegisterEntry
from register.services import build_workbook, sync_order, export_workbook


class RegisterWorkflowTestCase(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff_user",
            email="staff@example.com",
            password="StrongStaffPassword123!",
            is_staff=True,
        )
        self.customer = Customer.objects.create(
            name="Alpha Corp",
            email="alpha@example.com",
            phone="+919876543210",
        )
        self.plan = Plan.objects.create(
            name="Pro Plan",
            interval=Plan.Interval.MONTHLY,
        )
        self.product = Product.objects.create(
            name="Cloud Storage",
            sales_price=Decimal("500.00"),
            cost_price=Decimal("200.00"),
        )
        self.order = Order.objects.create(
            number="ORD-001",
            customer=self.customer,
            plan=self.plan,
            kind="subscription",
            status=Order.Status.CONFIRMED,
        )
        self.line = OrderLine.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("500.00"),
        )

    def test_sync_order_populates_register_entry(self):
        sync_order(self.order.pk)
        entry = RegisterEntry.objects.filter(order_id_ref=self.order.pk).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.customer_name, "Alpha Corp")
        self.assertEqual(entry.product, "Cloud Storage")
        self.assertEqual(entry.quantity, 2)
        self.assertEqual(entry.line_total, Decimal("1000.00"))

    def test_build_and_export_workbook(self):
        sync_order(self.order.pk)
        wb = build_workbook()
        self.assertIn("All Purchases", wb.sheetnames)
        self.assertIn("Subscriptions", wb.sheetnames)
        self.assertIn("Products", wb.sheetnames)
        
        path = export_workbook()
        self.assertTrue(path.endswith(".xlsx"))

    def test_download_register_view(self):
        sync_order(self.order.pk)
        client = Client()
        client.login(username="staff_user", password="StrongStaffPassword123!")
        response = client.get("/register/download/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
