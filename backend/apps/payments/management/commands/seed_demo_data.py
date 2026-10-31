from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User, UserRole
from apps.customers.models import Customer, CustomerType, CustomerStatus
from apps.subscriptions.models import Subscription, SubscriptionStatus, BillingInterval
from apps.billing.models import Invoice, InvoiceStatus
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.payments.services import record_payment
from apps.portal.models import CustomerRequest, RequestType
from apps.notifications.services import send_invoice_notification


class Command(BaseCommand):
    help = "Seeds real demo data for testing Payments, Portal, and Reporting."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Brightloop demo data...")

        # 1. Staff Users
        admin, _ = User.objects.get_or_create(
            email="admin@brightloop.io",
            defaults={
                "role": UserRole.ADMINISTRATOR,
                "first_name": "Sarah",
                "last_name": "Connor",
                "is_staff": True,
            }
        )
        admin.set_password("AdminSecure@123")
        admin.save()

        finance, _ = User.objects.get_or_create(
            email="finance@brightloop.io",
            defaults={
                "role": UserRole.FINANCE,
                "first_name": "Elena",
                "last_name": "Rostova",
                "is_staff": True,
            }
        )
        finance.set_password("FinanceSecure@123")
        finance.save()

        # 2. Customer 1 (Acme Corp)
        cust1_user, _ = User.objects.get_or_create(
            email="alice@acmecorp.com",
            defaults={
                "role": UserRole.CUSTOMER,
                "first_name": "Alice",
                "last_name": "Vance",
            }
        )
        cust1_user.set_password("CustomerSecure@123")
        cust1_user.save()

        acme, _ = Customer.objects.get_or_create(
            customer_code="CUST-ACME-01",
            defaults={
                "customer_type": CustomerType.BUSINESS,
                "display_name": "Acme Industrial Corp",
                "contact_person": "Alice Vance",
                "email": "alice@acmecorp.com",
                "phone": "+91 98450 12345",
                "billing_street": "42 Electronics City Phase 1",
                "billing_city": "Bengaluru",
                "billing_state": "Karnataka",
                "billing_postal_code": "560100",
                "billing_country": "India",
                "tax_identifier": "GSTIN-29AAAAA0000A1Z5",
                "payment_terms": "NET_30",
                "status": CustomerStatus.ACTIVE,
                "portal_user": cust1_user,
            }
        )

        # 3. Customer 2 (CloudScale Technologies)
        cust2_user, _ = User.objects.get_or_create(
            email="david@cloudscale.io",
            defaults={
                "role": UserRole.CUSTOMER,
                "first_name": "David",
                "last_name": "Miller",
            }
        )
        cust2_user.set_password("CustomerSecure@123")
        cust2_user.save()

        cloudscale, _ = Customer.objects.get_or_create(
            customer_code="CUST-CLOUD-02",
            defaults={
                "customer_type": CustomerType.BUSINESS,
                "display_name": "CloudScale Systems",
                "contact_person": "David Miller",
                "email": "david@cloudscale.io",
                "phone": "+91 91234 56789",
                "billing_street": "18 Cyber Gateway, Hitec City",
                "billing_city": "Hyderabad",
                "billing_state": "Telangana",
                "billing_postal_code": "500081",
                "billing_country": "India",
                "tax_identifier": "GSTIN-36BBBBB1111B2Z6",
                "payment_terms": "NET_15",
                "status": CustomerStatus.ACTIVE,
                "portal_user": cust2_user,
            }
        )

        today = timezone.now().date()

        # 4. Subscriptions
        sub_acme, _ = Subscription.objects.get_or_create(
            subscription_number="SUB-ACME-2026-001",
            defaults={
                "customer": acme,
                "plan_name": "Enterprise High-Voltage Power Engine",
                "billing_interval": BillingInterval.MONTHLY,
                "status": SubscriptionStatus.ACTIVE,
                "is_paused": False,
                "start_date": today - timedelta(days=90),
                "next_billing_date": today + timedelta(days=30),
                "currency": "INR",
            }
        )

        sub_cloud, _ = Subscription.objects.get_or_create(
            subscription_number="SUB-CLOUD-2026-002",
            defaults={
                "customer": cloudscale,
                "plan_name": "Industrial Grid Compute Core",
                "billing_interval": BillingInterval.MONTHLY,
                "status": SubscriptionStatus.ACTIVE,
                "is_paused": False,
                "start_date": today - timedelta(days=45),
                "next_billing_date": today + timedelta(days=15),
                "currency": "INR",
            }
        )

        # 5. Invoices for Acme Corp
        # Invoice 1: Past Paid
        inv1, _ = Invoice.objects.get_or_create(
            invoice_number="INV-2026-0001",
            defaults={
                "customer": acme,
                "subscription": sub_acme,
                "issue_date": today - timedelta(days=60),
                "due_date": today - timedelta(days=30),
                "subtotal": Decimal("25000.00"),
                "discount_total": Decimal("2500.00"),
                "tax_total": Decimal("4050.00"),
                "total_amount": Decimal("26550.00"),
                "outstanding_balance": Decimal("0.00"),
                "status": InvoiceStatus.PAID,
                "currency": "INR",
            }
        )
        if not Payment.objects.filter(invoice=inv1).exists():
            Payment.objects.create(
                invoice=inv1,
                customer=acme,
                recorded_by=finance,
                amount=Decimal("26550.00"),
                method=PaymentMethod.BANK_TRANSFER,
                status=PaymentStatus.SUCCEEDED,
                idempotency_key="seed-pay-acme-1",
                external_reference="NEFT-HDFC-991827",
                notes="Full advance settlement",
                paid_at=timezone.now() - timedelta(days=35),
            )

        # Invoice 2: Partially Paid (PRD Example: Total 10,000, 4,000 paid, 6,000 outstanding)
        inv2, _ = Invoice.objects.get_or_create(
            invoice_number="INV-2026-0002",
            defaults={
                "customer": acme,
                "subscription": sub_acme,
                "issue_date": today - timedelta(days=15),
                "due_date": today + timedelta(days=15),
                "subtotal": Decimal("10000.00"),
                "discount_total": Decimal("0.00"),
                "tax_total": Decimal("0.00"),
                "total_amount": Decimal("10000.00"),
                "outstanding_balance": Decimal("6000.00"),
                "status": InvoiceStatus.PARTIALLY_PAID,
                "currency": "INR",
            }
        )
        if not Payment.objects.filter(invoice=inv2).exists():
            Payment.objects.create(
                invoice=inv2,
                customer=acme,
                recorded_by=finance,
                amount=Decimal("4000.00"),
                method=PaymentMethod.UPI,
                status=PaymentStatus.SUCCEEDED,
                idempotency_key="seed-pay-acme-2",
                external_reference="UPI-AXIS-774411",
                notes="First installment received",
                paid_at=timezone.now() - timedelta(days=10),
            )

        # 6. Invoice for CloudScale (Overdue!)
        inv3, _ = Invoice.objects.get_or_create(
            invoice_number="INV-2026-0003",
            defaults={
                "customer": cloudscale,
                "subscription": sub_cloud,
                "issue_date": today - timedelta(days=35),
                "due_date": today - timedelta(days=5),  # OVERDUE!
                "subtotal": Decimal("15000.00"),
                "discount_total": Decimal("0.00"),
                "tax_total": Decimal("2700.00"),
                "total_amount": Decimal("17700.00"),
                "outstanding_balance": Decimal("17700.00"),
                "status": InvoiceStatus.CONFIRMED,
                "currency": "INR",
            }
        )

        send_invoice_notification(inv2)
        send_invoice_notification(inv3)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("Credentials:"))
        self.stdout.write(self.style.SUCCESS("  Finance Staff: finance@brightloop.io / FinanceSecure@123"))
        self.stdout.write(self.style.SUCCESS("  Admin Staff:   admin@brightloop.io / AdminSecure@123"))
        self.stdout.write(self.style.SUCCESS("  Customer Acme: alice@acmecorp.com / CustomerSecure@123"))
        self.stdout.write(self.style.SUCCESS("  Customer Cloud: david@cloudscale.io / CustomerSecure@123"))

