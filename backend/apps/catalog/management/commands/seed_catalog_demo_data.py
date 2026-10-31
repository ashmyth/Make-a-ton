from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import Product, ProductVariant, SubscriptionPlan, BillingInterval, StatusChoices
from apps.subscriptions.models import (
    QuotationTemplate,
    QuotationTemplateLine,
    Quotation,
    QuotationLine,
    QuotationStatus,
    Subscription,
    SubscriptionLine,
    SubscriptionStatus,
    OperationalStatus
)
from apps.customers.models import Customer


class Command(BaseCommand):
    help = "Seeds comprehensive commercial demo data for Teammate 2 (Products, Variants, Plans, Templates, Quotes, Subscriptions)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Teammate 2 Commercial Demo Data...")

        # 1. Products
        erp, _ = Product.objects.get_or_create(
            name="Enterprise ERP Suite",
            defaults={
                "type": "Software",
                "sales_price": Decimal("1000.00"),
                "cost_price": Decimal("400.00"),
                "notes": "Core ERP software application for industrial management.",
                "status": StatusChoices.ACTIVE,
            }
        )

        telemetry, _ = Product.objects.get_or_create(
            name="High-Voltage Telemetry Engine",
            defaults={
                "type": "Infrastructure",
                "sales_price": Decimal("4500.00"),
                "cost_price": Decimal("1800.00"),
                "notes": "Real-time edge telemetry and analytics infrastructure.",
                "status": StatusChoices.ACTIVE,
            }
        )

        support, _ = Product.objects.get_or_create(
            name="Dedicated Technical SLA & Support",
            defaults={
                "type": "Service",
                "sales_price": Decimal("750.00"),
                "cost_price": Decimal("250.00"),
                "notes": "24/7 dedicated engineering and incident response.",
                "status": StatusChoices.ACTIVE,
            }
        )

        # 2. Variants (including the exact PRD acceptance example: Odoo +560 => 1560)
        odoo_var, _ = ProductVariant.objects.get_or_create(
            product=erp,
            attribute_name="Brand",
            value="Odoo",
            defaults={
                "price_adjustment": Decimal("560.00"),
                "status": StatusChoices.ACTIVE,
            }
        )

        sap_var, _ = ProductVariant.objects.get_or_create(
            product=erp,
            attribute_name="Brand",
            value="SAP",
            defaults={
                "price_adjustment": Decimal("1200.00"),
                "status": StatusChoices.ACTIVE,
            }
        )

        hf_var, _ = ProductVariant.objects.get_or_create(
            product=telemetry,
            attribute_name="Sampling",
            value="100ms High-Frequency",
            defaults={
                "price_adjustment": Decimal("850.00"),
                "status": StatusChoices.ACTIVE,
            }
        )

        sla_p1, _ = ProductVariant.objects.get_or_create(
            product=support,
            attribute_name="Tier",
            value="24/7 Priority 1",
            defaults={
                "price_adjustment": Decimal("500.00"),
                "status": StatusChoices.ACTIVE,
            }
        )

        # 3. Subscription Plans
        enterprise_plan, _ = SubscriptionPlan.objects.get_or_create(
            name="Enterprise Industrial Monthly",
            defaults={
                "billing_interval": BillingInterval.MONTHLY,
                "min_quantity": 2,
                "allow_pause": True,
                "allow_early_closure": True,
                "allow_renewal": True,
                "auto_close_at_expiry": True,
                "default_payment_terms": "Net 30",
                "primary_product": erp,
                "default_primary_unit_price": Decimal("1000.00"),
                "status": StatusChoices.ACTIVE,
            }
        )

        starter_plan, _ = SubscriptionPlan.objects.get_or_create(
            name="Daily Grid Pilot",
            defaults={
                "billing_interval": BillingInterval.DAILY,
                "min_quantity": 1,
                "allow_pause": False,
                "allow_early_closure": False,
                "allow_renewal": True,
                "auto_close_at_expiry": True,
                "default_payment_terms": "Immediate",
                "primary_product": telemetry,
                "status": StatusChoices.ACTIVE,
            }
        )

        annual_plan, _ = SubscriptionPlan.objects.get_or_create(
            name="Annual Utility Scale Tier",
            defaults={
                "billing_interval": BillingInterval.YEARLY,
                "min_quantity": 3,
                "allow_pause": True,
                "allow_early_closure": False,
                "allow_renewal": True,
                "auto_close_at_expiry": False,  # Tests action-required queue
                "default_payment_terms": "Net 15",
                "status": StatusChoices.ACTIVE,
            }
        )

        # 4. Quotation Templates
        std_template, _ = QuotationTemplate.objects.get_or_create(
            name="Standard Industrial Package",
            defaults={
                "plan": enterprise_plan,
                "validity_days": 30,
                "notes": "Standard multi-facility package with ERP and 24/7 support.",
                "status": StatusChoices.ACTIVE,
            }
        )
        if not std_template.lines.exists():
            QuotationTemplateLine.objects.create(
                template=std_template,
                product=erp,
                variant=odoo_var,
                default_quantity=2,
                is_primary=True,
                sort_order=1
            )
            QuotationTemplateLine.objects.create(
                template=std_template,
                product=support,
                variant=sla_p1,
                default_quantity=1,
                is_primary=False,
                sort_order=2
            )

        today = timezone.now().date()

        # 5. Quotations
        # A. Confirmed Quote (Acme Corp)
        q_confirmed, _ = Quotation.objects.get_or_create(
            quotation_number="QT-2026-0001",
            defaults={
                "customer_id": "CUST-ACME-01",
                "template": std_template,
                "plan": enterprise_plan,
                "status": QuotationStatus.CONFIRMED,
                "issue_date": today - timedelta(days=15),
                "expiry_date": today + timedelta(days=15),
                "payment_terms": "Net 30",
                "confirmed_by": "Senior Account Lead",
                "confirmed_at": timezone.now() - timedelta(days=10),
            }
        )
        if not q_confirmed.lines.exists():
            QuotationLine.objects.create(
                quotation=q_confirmed,
                product=erp,
                variant=odoo_var,
                description="Enterprise ERP Suite (Brand: Odoo)",
                quantity=2,
                unit_price=Decimal("1560.00"),
                line_total=Decimal("3120.00"),
                is_primary=True,
                sort_order=1
            )
            QuotationLine.objects.create(
                quotation=q_confirmed,
                product=support,
                variant=sla_p1,
                description="Dedicated Technical SLA & Support (Tier: 24/7 Priority 1)",
                quantity=1,
                unit_price=Decimal("1250.00"),
                line_total=Decimal("1250.00"),
                is_primary=False,
                sort_order=2
            )

        # B. Expired Quote (ready for testing extension!)
        q_expired, _ = Quotation.objects.get_or_create(
            quotation_number="QT-2026-0002",
            defaults={
                "customer_id": "CUST-CLOUD-02",
                "plan": starter_plan,
                "status": QuotationStatus.EXPIRED,
                "issue_date": today - timedelta(days=45),
                "expiry_date": today - timedelta(days=5),
                "payment_terms": "Immediate",
            }
        )
        if not q_expired.lines.exists():
            QuotationLine.objects.create(
                quotation=q_expired,
                product=telemetry,
                variant=hf_var,
                description="High-Voltage Telemetry Engine (Sampling: 100ms High-Frequency)",
                quantity=1,
                unit_price=Decimal("5350.00"),
                line_total=Decimal("5350.00"),
                is_primary=True
            )

        # C. Draft Quote
        q_draft, _ = Quotation.objects.get_or_create(
            quotation_number="QT-2026-0003",
            defaults={
                "customer_id": "CUST-ACME-01",
                "plan": enterprise_plan,
                "status": QuotationStatus.DRAFT,
                "issue_date": today,
                "expiry_date": today + timedelta(days=30),
                "payment_terms": "Net 30",
            }
        )
        if not q_draft.lines.exists():
            QuotationLine.objects.create(
                quotation=q_draft,
                product=erp,
                variant=odoo_var,
                description="Enterprise ERP Suite (Brand: Odoo)",
                quantity=3,
                unit_price=Decimal("1560.00"),
                line_total=Decimal("4680.00"),
                is_primary=True
            )

        # 6. Active Subscriptions
        acme_cust = Customer.objects.filter(customer_code="CUST-ACME-01").first()

        # Subscription 1: Running
        sub_active, _ = Subscription.objects.get_or_create(
            subscription_number="SUB-2026-0001",
            defaults={
                "customer": acme_cust,
                "customer_id_ref": "CUST-ACME-01",
                "quotation": q_confirmed,
                "plan": enterprise_plan,
                "plan_name": enterprise_plan.name,
                "billing_interval": BillingInterval.MONTHLY,
                "status": SubscriptionStatus.ACTIVE,
                "is_paused": False,
                "start_date": today - timedelta(days=10),
                "billing_anchor_date": today - timedelta(days=10),
                "next_billing_date": today,  # Due today for Teammate 3 billing feed!
                "payment_terms": "Net 30",
            }
        )
        if not sub_active.lines.exists():
            SubscriptionLine.objects.create(
                subscription=sub_active,
                product=erp,
                variant=odoo_var,
                description="Enterprise ERP Suite (Brand: Odoo)",
                quantity=2,
                unit_price=Decimal("1560.00"),
                is_primary=True
            )
            SubscriptionLine.objects.create(
                subscription=sub_active,
                product=support,
                variant=sla_p1,
                description="Dedicated Technical SLA & Support (Tier: 24/7 Priority 1)",
                quantity=1,
                unit_price=Decimal("1250.00"),
                is_primary=False
            )

        # Subscription 2: Paused
        cloud_cust = Customer.objects.filter(customer_code="CUST-CLOUD-02").first()
        sub_paused, _ = Subscription.objects.get_or_create(
            subscription_number="SUB-2026-0002",
            defaults={
                "customer": cloud_cust,
                "customer_id_ref": "CUST-CLOUD-02",
                "plan": enterprise_plan,
                "plan_name": enterprise_plan.name,
                "billing_interval": BillingInterval.MONTHLY,
                "status": SubscriptionStatus.PAUSED,
                "is_paused": True,
                "start_date": today - timedelta(days=60),
                "billing_anchor_date": today - timedelta(days=60),
                "next_billing_date": today,
                "payment_terms": "Net 30",
                "pause_date": today - timedelta(days=7),
                "pause_reason": "Customer scheduled plant revamp.",
            }
        )
        if not sub_paused.lines.exists():
            SubscriptionLine.objects.create(
                subscription=sub_paused,
                product=erp,
                variant=sap_var,
                description="Enterprise ERP Suite (Brand: SAP)",
                quantity=2,
                unit_price=Decimal("2200.00"),
                is_primary=True
            )

        # Subscription 3: Expired without Auto-close (Enters Action Required queue)
        sub_action_req, _ = Subscription.objects.get_or_create(
            subscription_number="SUB-2026-0003",
            defaults={
                "customer": acme_cust,
                "customer_id_ref": "CUST-ACME-01",
                "plan": annual_plan,
                "plan_name": annual_plan.name,
                "billing_interval": BillingInterval.YEARLY,
                "status": SubscriptionStatus.ACTIVE,
                "is_paused": False,
                "action_required": True,
                "action_required_reason": f"Subscription expired on {today - timedelta(days=2)} without auto-close; renewal or closure required.",
                "start_date": today - timedelta(days=367),
                "expiry_date": today - timedelta(days=2),
                "billing_anchor_date": today - timedelta(days=367),
                "next_billing_date": today - timedelta(days=2),
                "payment_terms": "Net 15",
            }
        )
        if not sub_action_req.lines.exists():
            SubscriptionLine.objects.create(
                subscription=sub_action_req,
                product=telemetry,
                variant=hf_var,
                description="High-Voltage Telemetry Engine (Sampling: 100ms High-Frequency)",
                quantity=3,
                unit_price=Decimal("5350.00"),
                is_primary=True
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded Teammate 2 Commercial Demo Data!"))

