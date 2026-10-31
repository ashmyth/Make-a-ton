from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import Product, ProductVariant, SubscriptionPlan, BillingInterval, StatusChoices
from .models import QuotationTemplate, QuotationTemplateLine, Quotation, QuotationLine, QuotationStatus


class QuotationTemplateModelTests(TestCase):
    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            name="Standard Plan",
            billing_interval=BillingInterval.MONTHLY,
            min_quantity=2
        )
        self.product = Product.objects.create(
            name="Cloud Server",
            sales_price=Decimal("100.00"),
            cost_price=Decimal("40.00")
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            attribute_name="RAM",
            value="32GB",
            price_adjustment=Decimal("50.00")
        )
        self.template = QuotationTemplate.objects.create(
            name="Server Starter Template",
            plan=self.plan,
            validity_days=15
        )
        self.template_line = QuotationTemplateLine.objects.create(
            template=self.template,
            product=self.product,
            variant=self.variant,
            default_quantity=2,
            is_primary=True
        )

    def test_duplicate_template(self):
        """
        Verifies template deep-copy functionality:
        Creates a new template and copies all product lines into new database rows.
        """
        duplicated = self.template.duplicate()
        self.assertNotEqual(duplicated.id, self.template.id)
        self.assertEqual(duplicated.name, "Server Starter Template (Copy)")
        self.assertEqual(duplicated.plan, self.plan)
        self.assertEqual(duplicated.validity_days, 15)
        # Verify lines are copied
        self.assertEqual(duplicated.lines.count(), 1)
        copied_line = duplicated.lines.first()
        self.assertEqual(copied_line.product, self.product)
        self.assertEqual(copied_line.variant, self.variant)
        self.assertEqual(copied_line.default_quantity, 2)
        self.assertTrue(copied_line.is_primary)

    def test_variant_product_mismatch_rejected(self):
        """Verifies template line cannot select a variant from a different product."""
        other_product = Product.objects.create(
            name="Different Product",
            sales_price=Decimal("50.00"),
            cost_price=Decimal("20.00")
        )
        invalid_line = QuotationTemplateLine(
            template=self.template,
            product=other_product,
            variant=self.variant  # belongs to self.product!
        )
        with self.assertRaises(ValidationError):
            invalid_line.clean()


class QuotationWorkflowTests(APITestCase):
    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            name="Pro Annual",
            billing_interval=BillingInterval.YEARLY,
            min_quantity=1,
            default_primary_unit_price=Decimal("900.00")  # PRD §7.4 override
        )
        self.product = Product.objects.create(
            name="Enterprise Software",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("300.00")
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            attribute_name="Brand",
            value="Odoo",
            price_adjustment=Decimal("560.00")
        )
        self.template = QuotationTemplate.objects.create(
            name="Enterprise Template",
            plan=self.plan,
            validity_days=30
        )
        self.template_line = QuotationTemplateLine.objects.create(
            template=self.template,
            product=self.product,
            variant=self.variant,
            default_quantity=2,
            is_primary=True
        )

    def test_create_quotation_from_template_api(self):
        """
        Verifies creating a quotation from a template:
        - Copies values into new quotation
        - Calculates dynamic expiry date: issue_date + validity_days
        - Snapshots commercial prices according to PRD §7.4
        """
        url = reverse('quotation-template-create-quotation', kwargs={'pk': self.template.id})
        payload = {
            "customer_id": "CUST-9999",
            "issue_date": str(date.today()),
            "notes": "Custom deal for enterprise"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data

        self.assertEqual(data['customer_id'], "CUST-9999")
        self.assertEqual(data['status'], QuotationStatus.DRAFT)
        # Expiry calculated dynamically: today + 30 days
        expected_expiry = date.today() + timedelta(days=30)
        self.assertEqual(data['expiry_date'], str(expected_expiry))

        # Check line pricing snapshot:
        # Plan default price (900.00) + variant adjustment (560.00) = 1460.00
        # Line total = 1460.00 * 2 = 2920.00
        lines = data['lines']
        self.assertEqual(len(lines), 1)
        self.assertEqual(Decimal(lines[0]['unit_price']), Decimal("1460.00"))
        self.assertEqual(Decimal(lines[0]['line_total']), Decimal("2920.00"))
        self.assertEqual(Decimal(data['total_amount']), Decimal("2920.00"))

    def test_prevent_expired_quotation_confirmation(self):
        """
        STRICT REQUIREMENT:
        Prevent expired quotations from being confirmed unless extended or reissued.
        """
        expired_date = date.today() - timedelta(days=5)
        quotation = Quotation.objects.create(
            quotation_number="QT-EXPIRED-001",
            customer_id="CUST-001",
            plan=self.plan,
            issue_date=expired_date - timedelta(days=30),
            expiry_date=expired_date
        )
        QuotationLine.objects.create(
            quotation=quotation,
            product=self.product,
            description="Enterprise Software",
            quantity=1,
            unit_price=Decimal("1000.00"),
            line_total=Decimal("1000.00"),
            is_primary=True
        )

        self.assertTrue(quotation.is_expired)

        # Attempt to confirm via API
        url = reverse('quotation-confirm', kwargs={'pk': quotation.id})
        response = self.client.post(url, {"confirmed_by": "Ops Manager"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", response.data['error'].lower())

        quotation.refresh_from_db()
        self.assertNotEqual(quotation.status, QuotationStatus.CONFIRMED)

    def test_extend_expired_quotation_allows_confirmation(self):
        """
        Verifies that extending an expired quotation allows it to be confirmed.
        """
        expired_date = date.today() - timedelta(days=2)
        quotation = Quotation.objects.create(
            quotation_number="QT-REISSUE-002",
            customer_id="CUST-002",
            plan=self.plan,
            issue_date=expired_date - timedelta(days=30),
            expiry_date=expired_date
        )
        QuotationLine.objects.create(
            quotation=quotation,
            product=self.product,
            description="Enterprise Software",
            quantity=1,
            unit_price=Decimal("1000.00"),
            line_total=Decimal("1000.00"),
            is_primary=True
        )

        # Extend by 14 days
        extend_url = reverse('quotation-extend', kwargs={'pk': quotation.id})
        extend_res = self.client.post(extend_url, {"additional_days": 14})
        self.assertEqual(extend_res.status_code, status.HTTP_200_OK)

        quotation.refresh_from_db()
        self.assertFalse(quotation.is_expired)

        # Now confirmation must succeed
        confirm_url = reverse('quotation-confirm', kwargs={'pk': quotation.id})
        confirm_res = self.client.post(confirm_url, {"confirmed_by": "Ops Lead"})
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)

        quotation.refresh_from_db()
        self.assertEqual(quotation.status, QuotationStatus.CONFIRMED)
        self.assertEqual(quotation.confirmed_by, "Ops Lead")
        self.assertIsNotNone(quotation.confirmed_at)

    def test_duplicate_template_api(self):
        """Verifies duplicating a template via POST /api/subscriptions/templates/{id}/duplicate/."""
        url = reverse('quotation-template-duplicate', kwargs={'pk': self.template.id})
        response = self.client.post(url, {"name": "Cloned Template"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Cloned Template")
        self.assertEqual(len(response.data['lines']), 1)



    def test_create_custom_quotation_from_scratch(self):
        """
        Part D Requirement:
        Staff creates quotations directly for customers with products, variants, and quantities.
        """
        url = reverse('quotation-list')
        payload = {
            "customer_id": "CUST-DIRECT-1",
            "plan": str(self.plan.id),
            "validity_days": 45,
            "notes": "Direct tailored quotation",
            "lines": [
                {
                    "product": str(self.product.id),
                    "variant": str(self.variant.id),
                    "quantity": 3,
                    "is_primary": True
                }
            ]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_id'], "CUST-DIRECT-1")
        self.assertEqual(response.data['status'], QuotationStatus.DRAFT)
        # Price calculation: 900 (plan primary override) + 560 (variant) = 1460; Total: 1460 * 3 = 4380
        self.assertEqual(Decimal(response.data['total_amount']), Decimal("4380.00"))

    def test_custom_quotation_minimum_quantity_enforced(self):
        """Part D Requirement: Validates required minimum quantities from plan."""
        strict_plan = SubscriptionPlan.objects.create(
            name="Strict 10-Seat Plan",
            billing_interval=BillingInterval.MONTHLY,
            min_quantity=10
        )
        url = reverse('quotation-list')
        payload = {
            "customer_id": "CUST-FAIL-QTY",
            "plan": str(strict_plan.id),
            "lines": [
                {
                    "product": str(self.product.id),
                    "quantity": 2,  # Only 2, but min is 10!
                    "is_primary": True
                }
            ]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("minimum quantity", str(response.data).lower())

    def test_quotation_review_and_status_workflow(self):
        """
        Part D Requirement:
        Support quotation review and confirmation workflow: Draft -> Sent -> Reviewed -> Confirmed.
        """
        quotation = Quotation.objects.create(
            quotation_number="QT-FLOW-101",
            customer_id="CUST-FLOW",
            plan=self.plan,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=30)
        )
        QuotationLine.objects.create(
            quotation=quotation,
            product=self.product,
            description="Enterprise Software",
            quantity=1,
            unit_price=Decimal("1000.00"),
            line_total=Decimal("1000.00"),
            is_primary=True
        )

        # 1. Draft -> Sent
        send_url = reverse('quotation-send', kwargs={'pk': quotation.id})
        res_send = self.client.post(send_url)
        self.assertEqual(res_send.status_code, status.HTTP_200_OK)
        self.assertEqual(res_send.data['status'], QuotationStatus.SENT)

        # 2. Sent -> Reviewed
        review_url = reverse('quotation-review', kwargs={'pk': quotation.id})
        res_review = self.client.post(review_url)
        self.assertEqual(res_review.status_code, status.HTTP_200_OK)
        self.assertEqual(res_review.data['status'], QuotationStatus.REVIEWED)

        # 3. Reviewed -> Confirmed
        confirm_url = reverse('quotation-confirm', kwargs={'pk': quotation.id})
        res_confirm = self.client.post(confirm_url, {"confirmed_by": "Senior Account Exec"})
        self.assertEqual(res_confirm.status_code, status.HTTP_200_OK)
        self.assertEqual(res_confirm.data['status'], QuotationStatus.CONFIRMED)

    def test_confirmed_quotation_cannot_be_modified(self):
        """
        Part D Requirement:
        Preserve confirmed quotation details and block modifications after confirmation.
        """
        quotation = Quotation.objects.create(
            quotation_number="QT-FROZEN-202",
            customer_id="CUST-FROZEN",
            plan=self.plan,
            status=QuotationStatus.CONFIRMED,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=30)
        )
        url = reverse('quotation-detail', kwargs={'pk': quotation.id})
        response = self.client.patch(url, {"notes": "Attempting illegal change"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot be modified", response.data['error'])

    def test_cancel_quotation_workflow(self):
        """Part D Requirement: Cancel quotations."""
        quotation = Quotation.objects.create(
            quotation_number="QT-CANCEL-303",
            customer_id="CUST-CANCEL",
            plan=self.plan,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=30)
        )
        cancel_url = reverse('quotation-cancel', kwargs={'pk': quotation.id})
        res = self.client.post(cancel_url, {"reason": "Customer changed mind"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], QuotationStatus.CANCELLED)

    def test_preserve_quotation_details_when_catalog_price_changes(self):
        """
        CRITICAL BUSINESS RULE:
        Existing quotation prices do NOT change if catalog prices change later.
        """
        # Create quote with product sales_price = 1000.00
        url = reverse('quotation-template-create-quotation', kwargs={'pk': self.template.id})
        res = self.client.post(url, {"customer_id": "CUST-SNAPSHOT"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        quote_id = res.data['id']
        original_line_total = Decimal(res.data['lines'][0]['line_total'])

        # Now change the product and plan prices drastically in the catalog
        self.product.sales_price = Decimal("9999.00")
        self.product.save()
        self.plan.default_primary_unit_price = Decimal("8888.00")
        self.plan.save()

        # Re-fetch the previously created quotation
        detail_url = reverse('quotation-detail', kwargs={'pk': quote_id})
        get_res = self.client.get(detail_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        # Verify the line total on the quotation is STILL the original snapshot!
        self.assertEqual(Decimal(get_res.data['lines'][0]['line_total']), original_line_total)



from .models import Subscription, SubscriptionLine, SubscriptionStatus, OperationalStatus


class SubscriptionManagementTests(APITestCase):
    def setUp(self):
        self.pausable_plan = SubscriptionPlan.objects.create(
            name="Pausable Business Plan",
            billing_interval=BillingInterval.MONTHLY,
            min_quantity=1,
            allow_pause=True,
            allow_renewal=True,
            allow_early_closure=True
        )
        self.non_pausable_plan = SubscriptionPlan.objects.create(
            name="Strict Annual Plan",
            billing_interval=BillingInterval.YEARLY,
            min_quantity=1,
            allow_pause=False,
            allow_renewal=False,
            allow_early_closure=False
        )
        self.product = Product.objects.create(
            name="Analytics Platform",
            sales_price=Decimal("500.00"),
            cost_price=Decimal("150.00")
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            attribute_name="Tier",
            value="Enterprise",
            price_adjustment=Decimal("200.00")
        )

        # Create confirmed quotation ready for conversion
        self.quotation = Quotation.objects.create(
            quotation_number="QT-CONFIRMED-901",
            customer_id="CUST-SUB-1",
            plan=self.pausable_plan,
            status=QuotationStatus.CONFIRMED,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
            payment_terms="Net 30"
        )
        self.qline = QuotationLine.objects.create(
            quotation=self.quotation,
            product=self.product,
            variant=self.variant,
            description="Analytics Platform (Tier: Enterprise)",
            quantity=2,
            unit_price=Decimal("700.00"),
            line_total=Decimal("1400.00"),
            is_primary=True
        )

    def test_convert_confirmed_quotation_to_subscription(self):
        """
        Part E Requirement:
        Convert confirmed quotations into active subscriptions with frozen commercial snapshot.
        """
        url = reverse('quotation-convert-to-subscription', kwargs={'pk': self.quotation.id})
        payload = {
            "start_date": str(date.today()),
            "expiry_date": str(date.today() + timedelta(days=365))
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data

        self.assertEqual(data['customer_id'], "CUST-SUB-1")
        self.assertEqual(data['status'], SubscriptionStatus.ACTIVE)
        self.assertEqual(data['operational_status'], OperationalStatus.RUNNING)
        self.assertEqual(data['payment_terms'], "Net 30")
        self.assertEqual(Decimal(data['total_recurring_amount']), Decimal("1400.00"))

        # Verify lines are copied
        self.assertEqual(len(data['lines']), 1)
        self.assertEqual(Decimal(data['lines'][0]['unit_price']), Decimal("700.00"))
        self.assertEqual(data['lines'][0]['quantity'], 2)

    def test_cannot_convert_unconfirmed_quotation(self):
        """Verifies unconfirmed quotations cannot be converted to subscriptions."""
        draft_quote = Quotation.objects.create(
            quotation_number="QT-DRAFT-999",
            customer_id="CUST-DRAFT",
            plan=self.pausable_plan,
            status=QuotationStatus.DRAFT,
            expiry_date=date.today() + timedelta(days=30)
        )
        url = reverse('quotation-convert-to-subscription', kwargs={'pk': draft_quote.id})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("only confirmed quotations", response.data['error'].lower())

    def test_pause_and_resume_when_plan_allows(self):
        """
        Part E Requirement:
        Support pause and resume where the plan permits it.
        """
        sub = Subscription.objects.create(
            subscription_number="SUB-PAUSE-001",
            customer_id="CUST-P",
            plan=self.pausable_plan,
            status=SubscriptionStatus.ACTIVE,
            operational_status=OperationalStatus.RUNNING,
            start_date=date.today(),
            billing_anchor_date=date.today(),
            next_billing_date=date.today() + timedelta(days=30),
            payment_terms="Net 15"
        )

        # 1. Pause
        pause_url = reverse('subscription-pause', kwargs={'pk': sub.id})
        res_pause = self.client.post(pause_url, {"reason": "Temporary customer hiatus"})
        self.assertEqual(res_pause.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pause.data['operational_status'], OperationalStatus.PAUSED)
        self.assertIsNotNone(res_pause.data['pause_date'])

        # 2. Resume
        resume_url = reverse('subscription-resume', kwargs={'pk': sub.id})
        res_resume = self.client.post(resume_url)
        self.assertEqual(res_resume.status_code, status.HTTP_200_OK)
        self.assertEqual(res_resume.data['operational_status'], OperationalStatus.RUNNING)
        self.assertIsNotNone(res_resume.data['resume_date'])

    def test_pause_rejected_when_plan_disallows(self):
        """
        Part E Requirement:
        Enforce plan rules - pause rejected if plan.allow_pause is False.
        """
        sub = Subscription.objects.create(
            subscription_number="SUB-STRICT-002",
            customer_id="CUST-S",
            plan=self.non_pausable_plan,  # allow_pause = False
            status=SubscriptionStatus.ACTIVE,
            operational_status=OperationalStatus.RUNNING,
            start_date=date.today(),
            billing_anchor_date=date.today(),
            next_billing_date=date.today() + timedelta(days=365),
            payment_terms="Immediate"
        )

        pause_url = reverse('subscription-pause', kwargs={'pk': sub.id})
        response = self.client.post(pause_url, {"reason": "Want to pause"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not permit pausing", response.data['error'])

    def test_renewal_creates_linked_successor(self):
        """
        Part E Requirement:
        Support renewal by creating a linked successor subscription.
        """
        sub = Subscription.objects.create(
            subscription_number="SUB-RENEW-003",
            customer_id="CUST-R",
            plan=self.pausable_plan,
            status=SubscriptionStatus.ACTIVE,
            operational_status=OperationalStatus.RUNNING,
            start_date=date.today() - timedelta(days=365),
            expiry_date=date.today(),
            billing_anchor_date=date.today() - timedelta(days=365),
            next_billing_date=date.today(),
            payment_terms="Net 30"
        )
        SubscriptionLine.objects.create(
            subscription=sub,
            product=self.product,
            description="Analytics Platform",
            quantity=5,
            unit_price=Decimal("500.00"),
            is_primary=True
        )

        renew_url = reverse('subscription-renew', kwargs={'pk': sub.id})
        payload = {
            "new_start_date": str(date.today()),
            "new_expiry_date": str(date.today() + timedelta(days=365))
        }
        res = self.client.post(renew_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        successor_data = res.data

        # Successor assertions
        self.assertEqual(str(successor_data['predecessor']), str(sub.id))
        self.assertEqual(successor_data['status'], SubscriptionStatus.ACTIVE)
        self.assertEqual(len(successor_data['lines']), 1)
        self.assertEqual(successor_data['lines'][0]['quantity'], 5)

        # Predecessor assertions: closed upon renewal
        sub.refresh_from_db()
        self.assertEqual(sub.status, SubscriptionStatus.CLOSED)
        self.assertIn("renewed", sub.closure_reason.lower())

    def test_teammate_3_billing_export_endpoint(self):
        """
        CRITICAL INTEGRATION TEST FOR TEAMMATE 3 (BILLING ENGINE):
        GET /api/subscriptions/due-for-billing/
        STRICT RULE:
        - Must return active & running due subscriptions.
        - Paused and closed subscriptions must NEVER be returned for billing!
        """
        today = date.today()

        # 1. Active & running, due today -> MUST BE INCLUDED
        sub_active_due = Subscription.objects.create(
            subscription_number="SUB-DUE-001",
            customer_id="CUST-1",
            plan=self.pausable_plan,
            status=SubscriptionStatus.ACTIVE,
            operational_status=OperationalStatus.RUNNING,
            start_date=today - timedelta(days=30),
            billing_anchor_date=today - timedelta(days=30),
            next_billing_date=today,
            payment_terms="Net 30"
        )
        SubscriptionLine.objects.create(
            subscription=sub_active_due,
            product=self.product,
            description="Analytics Platform",
            quantity=2,
            unit_price=Decimal("500.00"),
            is_primary=True
        )

        # 2. Paused subscription -> MUST BE EXCLUDED
        sub_paused = Subscription.objects.create(
            subscription_number="SUB-PAUSED-002",
            customer_id="CUST-2",
            plan=self.pausable_plan,
            status=SubscriptionStatus.ACTIVE,
            operational_status=OperationalStatus.PAUSED,  # PAUSED!
            start_date=today - timedelta(days=30),
            billing_anchor_date=today - timedelta(days=30),
            next_billing_date=today,
            payment_terms="Net 30"
        )

        # 3. Closed subscription -> MUST BE EXCLUDED
        sub_closed = Subscription.objects.create(
            subscription_number="SUB-CLOSED-003",
            customer_id="CUST-3",
            plan=self.pausable_plan,
            status=SubscriptionStatus.CLOSED,  # CLOSED!
            operational_status=OperationalStatus.RUNNING,
            start_date=today - timedelta(days=60),
            billing_anchor_date=today - timedelta(days=60),
            next_billing_date=today,
            payment_terms="Net 30"
        )

        # 4. Future subscription (not due yet) -> MUST BE EXCLUDED
        sub_future = Subscription.objects.create(
            subscription_number="SUB-FUTURE-004",
            customer_id="CUST-4",
            plan=self.pausable_plan,
            status=SubscriptionStatus.ACTIVE,
            operational_status=OperationalStatus.RUNNING,
            start_date=today,
            billing_anchor_date=today,
            next_billing_date=today + timedelta(days=30),  # Not due yet!
            payment_terms="Net 30"
        )

        # Call billing feed endpoint
        url = reverse('subscription-due-for-billing')
        response = self.client.get(f"{url}?as_of={today}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_subs = response.data

        # MUST contain exactly 1 subscription: sub_active_due
        returned_ids = [s['subscription_id'] for s in returned_subs]
        self.assertIn(str(sub_active_due.id), returned_ids)
        self.assertNotIn(str(sub_paused.id), returned_ids)
        self.assertNotIn(str(sub_closed.id), returned_ids)
        self.assertNotIn(str(sub_future.id), returned_ids)

        # Verify Teammate 3 required contract fields
        item = returned_subs[0]
        self.assertEqual(item['subscription_number'], "SUB-DUE-001")
        self.assertEqual(item['status'], "active")
        self.assertEqual(item['operational_status'], "running")
        self.assertEqual(item['billing_interval'], "monthly")
        self.assertEqual(len(item['lines']), 1)
        self.assertEqual(Decimal(item['lines'][0]['unit_price']), Decimal("500.00"))
        self.assertEqual(item['lines'][0]['quantity'], 2)

    def test_close_subscription_at_term_expiry_api(self):
        """
        Part E & Deliverable Requirement:
        Tests for subscription closure at term expiry via POST /api/subscriptions/subscriptions/{id}/close/
        """
        today = date.today()
        sub = Subscription.objects.create(
            subscription_number="SUB-CLOSE-TERM-001",
            customer_id="CUST-EXP",
            plan=self.non_pausable_plan,  # allow_early_closure=False
            status=SubscriptionStatus.ACTIVE,
            start_date=today - timedelta(days=365),
            expiry_date=today,  # Expired today -> Not early!
            billing_anchor_date=today - timedelta(days=365),
            next_billing_date=today,
            payment_terms="Immediate"
        )

        close_url = reverse('subscription-close', kwargs={'pk': sub.id})
        res = self.client.post(close_url, {"reason": "Term completed successfully"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], SubscriptionStatus.CLOSED)

        sub.refresh_from_db()
        self.assertEqual(sub.status, SubscriptionStatus.CLOSED)
        self.assertEqual(sub.closure_date, today)
        self.assertEqual(sub.closure_reason, "Term completed successfully")

    def test_early_closure_rejected_when_plan_disallows(self):
        """
        Part E & Deliverable Requirement:
        Tests that early closure is rejected with HTTP 400 if plan.allow_early_closure is False.
        """
        today = date.today()
        sub = Subscription.objects.create(
            subscription_number="SUB-EARLY-REJECT-002",
            customer_id="CUST-STRICT",
            plan=self.non_pausable_plan,  # allow_early_closure=False
            status=SubscriptionStatus.ACTIVE,
            start_date=today,
            expiry_date=today + timedelta(days=180),  # In future!
            billing_anchor_date=today,
            next_billing_date=today + timedelta(days=30),
            payment_terms="Immediate"
        )

        close_url = reverse('subscription-close', kwargs={'pk': sub.id})
        res = self.client.post(close_url, {"reason": "Customer cancellation attempt"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not permit early closure", res.data['error'])

        sub.refresh_from_db()
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)

    def test_early_closure_allowed_when_plan_permits(self):
        """
        Part E & Deliverable Requirement:
        Tests that early closure succeeds when plan.allow_early_closure is True.
        """
        today = date.today()
        sub = Subscription.objects.create(
            subscription_number="SUB-EARLY-OK-003",
            customer_id="CUST-FLEX",
            plan=self.pausable_plan,  # allow_early_closure=True
            status=SubscriptionStatus.ACTIVE,
            start_date=today,
            expiry_date=today + timedelta(days=180),  # In future!
            billing_anchor_date=today,
            next_billing_date=today + timedelta(days=30),
            payment_terms="Immediate"
        )

        close_url = reverse('subscription-close', kwargs={'pk': sub.id})
        res = self.client.post(close_url, {"reason": "Customer downsizing"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], SubscriptionStatus.CLOSED)

        sub.refresh_from_db()
        self.assertEqual(sub.status, SubscriptionStatus.CLOSED)
        self.assertEqual(sub.closure_reason, "Customer downsizing")

    def test_early_closure_forced_with_early_flag(self):
        """
        Part E & Deliverable Requirement:
        Staff explicitly forces early closure with early=True flag.
        """
        today = date.today()
        sub = Subscription.objects.create(
            subscription_number="SUB-EARLY-FLAG-004",
            customer_id="CUST-FORCE",
            plan=self.non_pausable_plan,  # allow_early_closure=False
            status=SubscriptionStatus.ACTIVE,
            start_date=today,
            expiry_date=today + timedelta(days=90),
            billing_anchor_date=today,
            next_billing_date=today + timedelta(days=30),
            payment_terms="Immediate"
        )

        close_url = reverse('subscription-close', kwargs={'pk': sub.id})
        res = self.client.post(close_url, {"reason": "Executive special waiver", "early": True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sub.refresh_from_db()
        self.assertEqual(sub.status, SubscriptionStatus.CLOSED)

    def test_cannot_close_already_closed_subscription(self):
        """Tests that closing an already closed subscription returns HTTP 400."""
        today = date.today()
        sub = Subscription.objects.create(
            subscription_number="SUB-ALREADY-CLOSED-005",
            customer_id="CUST-CLOSED",
            plan=self.pausable_plan,
            status=SubscriptionStatus.CLOSED,
            closure_date=today,
            closure_reason="Previous closure"
        )
        close_url = reverse('subscription-close', kwargs={'pk': sub.id})
        res = self.client.post(close_url, {"reason": "Duplicate close call"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already closed", res.data['error'].lower())

    def test_auto_close_at_expiry_sweep_service_and_api(self):
        """
        Part B Requirement (100%):
        Automated sweep for auto_close_at_expiry:
        - Subscriptions under auto_close_at_expiry=True plans are automatically closed.
        - Subscriptions under auto_close_at_expiry=False plans enter action_required queue.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        auto_close_plan = SubscriptionPlan.objects.create(
            name="Auto Close Expired Plan",
            billing_interval=BillingInterval.MONTHLY,
            auto_close_at_expiry=True
        )
        manual_review_plan = SubscriptionPlan.objects.create(
            name="Manual Review Expired Plan",
            billing_interval=BillingInterval.MONTHLY,
            auto_close_at_expiry=False
        )

        sub_auto = Subscription.objects.create(
            subscription_number="SUB-SWEEP-AUTO-001",
            customer_id="CUST-SWEEP-1",
            plan=auto_close_plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=yesterday - timedelta(days=30),
            expiry_date=yesterday,
            billing_anchor_date=yesterday - timedelta(days=30),
            next_billing_date=today
        )

        sub_manual = Subscription.objects.create(
            subscription_number="SUB-SWEEP-MANUAL-002",
            customer_id="CUST-SWEEP-2",
            plan=manual_review_plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=yesterday - timedelta(days=30),
            expiry_date=yesterday,
            billing_anchor_date=yesterday - timedelta(days=30),
            next_billing_date=today
        )

        # Trigger sweep via API action: POST /api/subscriptions/subscriptions/sweep-expiries/
        sweep_url = reverse('subscription-sweep-expiries')
        res = self.client.post(sweep_url, {"as_of": str(today)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['auto_closed_count'], 1)
        self.assertEqual(res.data['action_required_count'], 1)
        self.assertIn(sub_auto.subscription_number, res.data['auto_closed_subscriptions'])
        self.assertIn(sub_manual.subscription_number, res.data['action_required_subscriptions'])

        # Verify database state
        sub_auto.refresh_from_db()
        self.assertEqual(sub_auto.status, SubscriptionStatus.CLOSED)
        self.assertIn("auto-closed at expiry", sub_auto.closure_reason)

        sub_manual.refresh_from_db()
        self.assertEqual(sub_manual.status, SubscriptionStatus.ACTIVE)
        self.assertTrue(sub_manual.action_required)
        self.assertIn("renewal or closure required", sub_manual.action_required_reason)

        # PRD §7.7 Verification: Billing MUST STOP for action-required subscription!
        billing_url = reverse('subscription-due-for-billing')
        billing_res = self.client.get(f"{billing_url}?as_of={today}")
        self.assertEqual(billing_res.status_code, status.HTTP_200_OK)
        due_ids = [s['subscription_id'] for s in billing_res.data]
        self.assertNotIn(str(sub_auto.id), due_ids)
        self.assertNotIn(str(sub_manual.id), due_ids)

    def test_customer_code_resolved_to_foreign_key_on_conversion(self):
        """
        Integration Responsibility (100%):
        Ensures customer code (e.g. 'CUST-ALPHA-99') resolves to Customer ForeignKey
        so Teammate 4's Customer Portal can seamlessly filter subscriptions by customer.
        """
        from apps.customers.models import Customer
        customer = Customer.objects.create(
            customer_code="CUST-ALPHA-99",
            display_name="Alpha Tech Industries",
            email="finance@alphatech.com"
        )

        # Create quote with customer_code instead of UUID
        quote = Quotation.objects.create(
            quotation_number="QT-INTEG-001",
            customer_id="CUST-ALPHA-99",
            plan=self.pausable_plan,
            status=QuotationStatus.CONFIRMED,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=30)
        )
        QuotationLine.objects.create(
            quotation=quote,
            product=self.product,
            quantity=1,
            unit_price=Decimal("500.00"),
            line_total=Decimal("500.00"),
            is_primary=True
        )

        # Convert to subscription
        convert_url = reverse('quotation-convert-to-subscription', kwargs={'pk': quote.id})
        res = self.client.post(convert_url, {"start_date": str(date.today())})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        sub = Subscription.objects.get(id=res.data['id'])
        # Foreign key MUST be linked to the Customer object!
        self.assertEqual(sub.customer, customer)
        self.assertEqual(str(sub.customer_id), str(customer.id))
        self.assertEqual(sub.customer_id_ref, "CUST-ALPHA-99")
