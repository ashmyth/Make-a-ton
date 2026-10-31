# Billing App Integration Notice

The standalone prototype from `Invoice_Generator/` has been unified into the main Django project at:
`backend/apps/billing/`

### Key Highlights of the Unified Implementation:
1. **Full PRD §7.8, §7.9, §7.12 & BILL-01..08 Compliance:**
   - Idempotent recurring billing engine (`backend/apps/billing/services/recurring.py`).
   - Atomic row-locking allocation & reversal (`backend/apps/billing/services/allocation.py`).
   - Gap-safe contiguous sequence numbering (`InvoiceSequence`).
   - Itemized decimal line calculations with ROUND_HALF_UP (`backend/apps/billing/services/calculation.py`).
2. **Customer Model Alignment (PRD §7.2):**
   - Links to CRM `Customer` model while supporting optional portal user logins.
   - Preserves snapshot fields (`customer_name`, `customer_email`, `billing_address`, `subscription_id`, `subscription_number`).
3. **Operational Commands:**
   - `python manage.py run_billing_sweep [--as-of YYYY-MM-DD]`
   - `python manage.py retry_failed_invoices`
4. **Staff Dashboard & Preview:**
   - Mounted at `/billing/invoices/`, `/billing/invoices/<id>/`, `/billing/invoices/<id>/pdf/`, etc.
5. **Automated Test Suite:**
   - Run via: `cd backend && python manage.py test apps.billing.tests`

