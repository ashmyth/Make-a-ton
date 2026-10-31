# Product Requirements Document: Brightloop Subscription Management Platform

**Version:** 1.0
**Status:** Proposed implementation specification
**Product type:** Web application with an internal operations console and a customer portal
**Primary users:** Administrators, internal staff, customers, and finance users

---

## 1. Purpose and Requirement Interpretation

Build a unified platform that manages Brightloop's subscription business from product configuration and quotations through recurring invoicing, payment tracking, and financial reporting.

The supplied assignment establishes the core requirements: account management, role-based access, products and variants, recurring plans, quotation templates, subscription lifecycles, automated invoices, tax and discount rules, payments, customer visibility, and reporting. Pages must respond in under two seconds with thousands of subscriptions.

This PRD distinguishes between:

- **Required:** Explicitly stated in the assignment.
- **Proposed:** A design decision added to make the requirements implementable.
- **Open:** A business decision that requires confirmation.

Unless otherwise noted, detailed behavior beyond the assignment's stated capabilities is proposed rather than an additional source requirement.

---

## 2. Problem Statement

Brightloop currently uses disconnected, manual processes:

| Current Process | Business Problem |
| --- | --- |
| Spreadsheet-based subscription tracking | Unclear subscription status and inconsistent records |
| Manually remembered renewals | Missed renewals |
| Manually prepared invoices | Incorrect or delayed billing |
| Bank-statement-based payment matching | Difficult payment reconciliation |
| Manually compiled revenue reports | Slow and unreliable financial visibility |

The platform must replace these processes with connected records, controlled workflows, recurring billing automation, and a consolidated reporting interface.

---

## 3. Product Goals

### 3.1 Business Goals

- Maintain one reliable record of every customer subscription.
- Generate recurring invoices without manual re-entry.
- Prevent duplicate billing and make missed billing visible.
- Track payments and remaining invoice balances.
- Apply eligible taxes and discounts consistently.
- Give customers access to their own subscription and invoice information.
- Provide timely visibility into subscriptions, collections, and overdue balances.

### 3.2 Proposed Success Measures

These are acceptance targets, not existing business performance figures.

| Measure | Proposed Target |
| --- | --- |
| Duplicate recurring invoices | Zero for the same subscription and billing period |
| Untracked billing failures | Zero; failures appear in an operations queue |
| Invoice calculation accuracy | All approved financial test cases pass |
| Unauthorized customer record access | Zero in access-control tests |
| Dashboard consistency | Totals reconcile with the underlying invoice and payment records |
| Page response performance | Meet the assignment's under-two-second requirement under an agreed load test |
| Billing recoverability | Retrying interrupted processing does not create duplicates |

---

## 4. Users and Permissions

The assignment defines administrators, internal staff, and customers. Only administrators can add staff and create discount rules; customers must see only their own subscriptions and invoices.

### 4.1 Proposed Permission Model

Finance is a staff permission profile, not a separate required account type.

| Capability | Admin | Operations Staff | Finance Staff | Customer |
| --- | --- | --- | --- | --- |
| Manage staff accounts and permissions | Yes | No | No | No |
| Manage products and variants | Yes | View | View | No |
| Manage plans | Yes | View | View | View applicable information |
| Manage taxes and discount rules | Yes | View | View | No |
| Manage customers | Yes | Yes | View | Own profile only |
| Manage quotation templates | Yes | Yes | View | No |
| Create quotations and subscriptions | Yes | Yes | View | No |
| Activate, pause, renew, or close subscriptions | Yes | With permission | View | View own |
| View invoices | All | All | All | Own only |
| Confirm, send, print, or cancel invoices | Yes | With permission | With permission | Download own only |
| Record payments | Yes | With permission | Yes | No |
| View financial reporting | Yes | Limited | Yes | No |

All permissions must be enforced by the backend, not merely by hiding interface elements.

### 4.2 Customer Self-Service Boundary

The assignment says customers should manage subscriptions through a portal but does not define which changes they can make.

**Proposed initial scope:**

- View subscription details and renewal information.
- View and download invoices.
- View recorded payments and outstanding balances.
- Update permitted profile fields.
- Submit pause, cancellation, or renewal requests.

Direct customer changes to seats, plans, or subscription status remain out of scope until their financial effects are defined.

---

## 5. Scope and Boundaries

### 5.1 Initial Release

- Authentication and password recovery.
- Role-based access.
- Customer management.
- Product and variant catalog.
- Subscription plans.
- Tax and discount configuration.
- Quotation templates and subscription quotations.
- Subscription lifecycle management.
- Automated recurring invoice creation.
- Invoice confirmation, cancellation, sending, and printing.
- Manual payment recording and allocation.
- Outstanding and overdue invoice tracking.
- Customer portal.
- Dashboard, filters, and summary reporting.
- Audit history and billing failure visibility.

### 5.2 Proposed Exclusions

The assignment does not explicitly require the following:

- Payment gateway integration.
- Automatic bank reconciliation.
- Full accounting or general-ledger functionality.
- Accounting revenue recognition schedules.
- Multi-currency conversion.
- Usage-based metering.
- Automatic prorated upgrades and downgrades.
- Refund processing and credit-note workflows.
- Integration with Odoo or another business system.
- Multiple independent businesses operating within one deployment.

These should not be silently included in the initial release.

---

## 6. End-to-End Workflow

```
Admin configures products, variants, plans, taxes, and discounts
        ↓
Customer registers, or staff creates a customer record
        ↓
Staff creates a quotation using a template
        ↓
Quotation is reviewed and confirmed
        ↓
Subscription becomes active
        ↓
Scheduled billing finds a due subscription
        ↓
Invoice is generated with price, discount, and tax snapshots
        ↓
Authorized staff confirms and sends the invoice
        ↓
Payment is recorded and allocated
        ↓
Invoice balance and reporting update
        ↓
Next billing cycle, pause, renewal, or closure
```

This flow connects the assignment's required subscription, billing, payment, and reporting capabilities.

---

## 7. Functional Requirements

### 7.1 Authentication and Account Management

**Required account rules:**

- Each email belongs to only one account.
- Passwords contain at least nine characters, including an uppercase letter, lowercase letter, and special character.
- Password reset links are sent to the registered email.
- Only administrators create staff accounts.

**Proposed implementation requirements:**

| ID | Requirement |
| --- | --- |
| AUTH-01 | Normalize email addresses consistently for uniqueness checks. |
| AUTH-02 | Store password hashes, never plaintext passwords. |
| AUTH-03 | Use single-use, expiring password-reset tokens. |
| AUTH-04 | Use neutral reset responses that do not reveal whether an email exists. |
| AUTH-05 | Allow administrators to deactivate staff access without deleting historical records. |
| AUTH-06 | Apply login throttling and secure session handling. |
| AUTH-07 | Link customer users to the correct customer record. |

**Acceptance criteria:**

- A duplicate email cannot create a second account.
- A password failing any stated rule is rejected.
- An expired or reused reset link fails.
- A customer cannot access another customer's data by changing a URL or API identifier.

### 7.2 Customer Management

**Proposed customer fields:**

- Customer ID
- Individual or business display name
- Contact person
- Email and optional phone
- Billing address
- Tax identifier, if applicable
- Default payment terms
- Active or archived status
- Linked portal account

**Requirements:**

- Staff can search customers and review associated quotations, subscriptions, invoices, and payments.
- Customers referenced by financial records cannot be permanently deleted.
- Changing a customer's billing details does not rewrite previously confirmed invoices.
- A staff-created customer can exist without a portal login.

### 7.3 Products and Variants

The assignment requires product name, type, sales price, cost price, notes, and variants with price adjustments; its example adds 560 for an Odoo brand variant.

**Proposed fields and behavior:**

| Field | Behavior |
| --- | --- |
| Product ID | System-generated |
| Name | Required |
| Type | Configurable category |
| Sales price | Non-negative monetary value |
| Cost price | Internal-only value |
| Notes | Optional |
| Variant attributes | For example, Brand |
| Variant values | For example, Odoo |
| Price adjustment | Added to the base product price |
| Status | Active or archived |

**Requirements:**

- Staff can select an active product and valid variant combination on a quotation line.
- Cost prices are not visible in the customer portal.
- Archiving prevents new selection but preserves historical references.
- Existing subscription prices do not change automatically when catalog prices change.

**Acceptance example:** For an illustrative base price of 1,000 and a variant adjustment of 560, the default unit price is 1,560 before discounts and taxes.

### 7.4 Subscription Plans

Required plan capabilities include price, daily/weekly/monthly/yearly billing, minimum quantity, availability dates, and configurable pause, renewal, early closure, and automatic end-of-term closure behavior.

**Proposed fields:**

- Plan ID and name
- Billing interval
- Minimum quantity
- Availability start and end
- Auto-close at subscription expiry
- Allow pause
- Allow early closure
- Allow renewal
- Default payment terms
- Active or archived status

**Pricing decision:**

The assignment gives both products and plans prices but does not specify how those prices combine. Proposed initial rule:

- Subscription line unit prices are the source of recurring charges.
- A plan may define a default per-unit price for a designated primary product.
- That default replaces the primary product's base price before variant adjustments.
- Add-ons use their own product prices.
- The plan price is not added again as a separate charge.
- The quotation displays the resulting prices before confirmation.

If a different interpretation is required, it must be approved before pricing implementation.

### 7.5 Quotation Templates

**Required:** Templates contain the applicable plan, product lines, and a validity duration in days.

**Proposed requirements:**

- Create, edit, archive, and duplicate templates.
- Define default products, quantities, and permitted price defaults.
- Calculate quotation expiry from its issue date and validity duration.
- Copy template values into the quotation.
- Preserve existing quotations when a template changes.
- Block expired quotations from confirmation until an authorized user extends or reissues them.

### 7.6 Subscription Records

**Required fields** include subscription number, customer, plan, start date, expiry date, payment terms, and lines containing product, quantity, unit price, tax, and amount.

**Additional proposed fields:**

- Billing anchor date
- Next billing date
- Last successfully generated billing period
- Renewal linkage
- Pause date and reason
- Closure date and reason
- Applied discount references
- Record version for concurrent updates
- Created by, created at, and updated at

**Requirements:**

- Subscription numbers are unique and not reused.
- Minimum quantities are validated before confirmation.
- Start dates cannot exceed expiry dates.
- At least one valid billable line is required for activation.
- Confirmed commercial terms are preserved as a snapshot.

### 7.7 Subscription Lifecycle

The required sequence is Draft → Quotation → Confirmed → Active → Closed. Pausing is also required where the plan permits it.

**Proposed model:**

- Lifecycle: Draft, Quotation, Confirmed, Active, Closed.
- Operational condition while active: Running or Paused.

| Transition | Proposed Condition |
| --- | --- |
| Draft → Quotation | Customer, plan, and valid lines exist |
| Quotation → Confirmed | Quotation is valid and required fields pass validation |
| Confirmed → Active | Start date has arrived and an authorized activation occurs |
| Active/Running → Active/Paused | Plan allows pausing |
| Active/Paused → Active/Running | Authorized resume |
| Active → Closed | Expiry closure or permitted early closure |

**Proposed rules:**

- Closed subscriptions generate no new billing periods.
- Paused subscriptions generate no new invoices while paused.
- Already-issued invoices remain payable after pause or closure.
- Renewal creates a linked successor subscription, preserving the original record.
- If expiry is reached without automatic closure, billing stops and the subscription appears in an "Expired—action required" queue.
- Pause/resume scheduling and prepaid-service adjustments require explicit approval before release.

### 7.8 Automated Recurring Billing

**Required:** Generate invoices from due subscriptions, populate customer and line details, apply taxes, and avoid duplicate or skipped billing.

**Proposed processing flow:**

1. Find eligible active, running subscriptions.
2. Determine each due service period.
3. Check whether an invoice already exists for that period.
4. Resolve pricing and eligible discounts.
5. Calculate totals.
6. Save the invoice and immutable calculation details.
7. Advance the billing checkpoint.
8. Record success or a visible failure.

**Requirements:**

| ID | Requirement |
| --- | --- |
| BILL-01 | Use a unique billing identity based on subscription and service-period boundaries. |
| BILL-02 | Make invoice creation and checkpoint advancement atomic. |
| BILL-03 | Allow safe retries after crashes or timeouts. |
| BILL-04 | Process subscriptions independently so one failure does not block the batch. |
| BILL-05 | Show failed runs, affected subscriptions, error details, and retry controls. |
| BILL-06 | Recover missed periods after downtime without combining them invisibly. |
| BILL-07 | Avoid generating periods beyond the subscription expiry. |
| BILL-08 | Never silently create prorated charges without an approved policy. |

**Proposed billing convention:**

- Bill in advance on the subscription start-date anchor.
- Clamp monthly dates to the last valid day of shorter months.
- Preserve the original anchor for later months.
- Use one configured business timezone.
- Final partial periods and expiry alignment remain open decisions.

### 7.9 Invoice Management

**Required invoice actions** are confirm, cancel, send, and print; the stated lifecycle is Draft → Confirmed → Paid.

**Proposed invoice fields:**

- Invoice number
- Customer and billing-address snapshot
- Subscription reference
- Service-period start and end
- Issue date and due date
- Product and variant descriptions
- Quantities and unit prices
- Discount and tax breakdowns
- Subtotal, discount total, tax total, grand total
- Allocated payments and outstanding balance
- Currency and status

**Proposed rules:**

- Add Cancelled as a terminal state.
- Keep partially paid invoices Confirmed, with a separate "Partially paid" indicator.
- Treat overdue as a derived condition, not a lifecycle state.
- Prevent cancellation when payment allocations exist.
- Do not allow financial edits after confirmation.
- Log sending attempts separately from invoice status.
- Generate printable and downloadable invoice PDFs.
- Do not silently regenerate a cancelled invoice for the same service period; require an explicit replacement process.

### 7.10 Tax Calculation

**Required:** Admin-configured tax rules are applied automatically.

**Proposed initial scope:**

- Percentage-based, tax-exclusive rules.
- One tax rule per invoice line.
- Optional applicability by product.
- Effective start and end dates.
- Explicit zero-tax treatment where applicable.
- Fixed rounding rules for the configured currency.
- Confirmed invoice tax snapshots.

Jurisdiction-based tax compliance, compound taxes, exemptions, and tax-inclusive pricing require separate definition.

### 7.11 Discount Management

**Required discount properties** include fixed amount or percentage, minimum purchase or quantity, validity dates, usage limit, and product-level or subscription-level application. Discounts apply automatically to the next eligible invoice and stop when expired or exhausted.

**Proposed rules:**

- Only admins create or edit discount definitions.
- Eligibility is checked using the invoice issue date in the business timezone.
- Thresholds are evaluated before discount and tax.
- Discounts cannot reduce an eligible subtotal below zero.
- Do not stack discounts initially.
- If several discounts qualify, select the eligible rule producing the greatest reduction.
- Allocate a subscription-wide fixed discount across eligible lines proportionally.
- Reserve limited-use discounts during draft invoice creation.
- Consume a use on confirmation.
- Release the reservation when the draft is cancelled.
- Preserve confirmed usage history after cancellation unless an admin explicitly restores it.
- The reservation mechanism must prevent parallel billing jobs from exceeding a usage limit.

### 7.12 Payment Recording and Allocation

**Required payment information:** method, amount, date, note, and the invoice receiving the payment.

**Proposed implementation requirements:**

| ID | Requirement |
| --- | --- |
| PAY-01 | **Invoice-first allocation:** Payments are allocated strictly to existing confirmed invoices; payments never generate invoices. |
| PAY-02 | **Idempotent recording:** Enforce idempotency via a unique `idempotency_key` on all payment submissions to prevent duplicate recording from retries or double clicks. |
| PAY-03 | **Overpayment protection:** Reject any payment allocation that exceeds the target invoice's remaining `outstanding_balance`. Enforce row-level locking during allocation. |
| PAY-04 | **Immutable ledger & audited reversals:** Recorded payments cannot be permanently deleted. Corrections require an audited reversal record restoring invoice balance. |
| PAY-05 | **Atomic balance & status sync:** Allocations and reversals atomically update `invoice.outstanding_balance` and status (`Confirmed` ↔ `Partially paid` ↔ `Paid`). |
| PAY-06 | **Gateway-ready schema:** Store payment method, currency, and optional external references (bank UTR, cheque number, or future gateway payment ID) to support automated gateways in V2 without schema redesign. |

**Proposed behavior:**

- Allow multiple payments against one invoice.
- Support partial payments.
- Initially allocate each payment to one invoice.
- Reject allocations exceeding the outstanding balance.
- Record an optional external reference.
- Do not permanently delete recorded payments.
- Use an audited reversal to correct a payment.
- Recalculate invoice balance and payment status after allocation or reversal.

**Acceptance example:** For an invoice total of 1,000, a payment of 400 leaves 600 outstanding. A second payment of 600 marks the invoice Paid.

### 7.13 Reporting and Dashboard

**Required reporting** includes active subscriptions, revenue, payments, amounts owed, overdue invoices, filters, and summaries.

**Proposed metric definitions:**

| Metric | Definition |
| --- | --- |
| Active subscriptions | Lifecycle is Active, including paused subscriptions |
| Running subscriptions | Active subscriptions not paused |
| Billed amount | Confirmed and Paid invoice totals issued in the selected period, excluding cancelled invoices |
| Cash collected | Recorded payments dated in the selected period, net of reversals |
| Outstanding balance | Unpaid balance across non-cancelled confirmed invoices |
| Overdue balance | Outstanding balance where the due date is before today |
| Overdue invoice count | Number of invoices meeting the overdue definition |

"Billed amount" and "cash collected" must remain separate; neither should be presented as accounting revenue recognition.

**Filters:** date range, customer, plan, subscription status, invoice status, payment method, and overdue condition.

Each date filter must state which date it uses, for example invoice issue date versus payment date.

### 7.14 Notifications

The assignment explicitly requires password-reset email and the ability to send invoices.

**Proposed notifications:**

- Password-reset email
- Quotation email
- Invoice email with PDF or secure portal access
- Payment receipt
- Upcoming expiry notice
- Overdue reminder

Only password reset and invoice sending are required for the initial acceptance scope. Optional reminders should be configurable and logged.

---

## 8. Proposed Calculation Specification

**For each invoice line:**

- **Gross line amount** = Quantity × Unit price
- **Taxable line amount** = Gross line amount − Allocated discount
- **Line tax** = Taxable line amount × Tax rate

**For the invoice:**

- **Invoice total** = Σ (Taxable line amount + Line tax)
- **Outstanding balance** = Invoice total − Net allocated payments

**Proposed calculation policies:**

- Use decimal monetary arithmetic.
- Round each line's tax to the configured currency precision.
- Sum rounded line amounts for invoice totals.
- Preserve calculation inputs on confirmed invoices.
- Apply discounts before taxes.
- Use the same calculation service for previews and saved invoices.

**Illustrative example** (these prices and tax rates are examples, not values specified by the assignment):

| Component | Amount |
| --- | --- |
| 10 seats × 500 | 5,000 |
| 10% discount | −500 |
| Taxable amount | 4,500 |
| Illustrative 10% tax | 450 |
| Invoice total | 4,950 |
| Payment received | −3,000 |
| Outstanding | 1,950 |
