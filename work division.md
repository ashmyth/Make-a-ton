# Brightloop --- Work Division (4 Teammates)

**Project:** Brightloop Subscription Management Platform\
**Document purpose:** Divide the project into four independently owned
workstreams, with clear responsibilities, deliverables, boundaries, and
integration points.\
**Important:** This document intentionally does **not** prescribe a
technology stack. Each teammate should research, select, and justify the
technologies for their own workstream, then coordinate compatibility
with the rest of the team.

------------------------------------------------------------------------

## 1. Team ownership at a glance

  -----------------------------------------------------------------------
  Teammate                Workstream              Primary ownership
  ----------------------- ----------------------- -----------------------
  **Teammate 1**          Identity, access, and   Authentication, roles
                          customer foundation     and permissions, staff
                                                  accounts, customer
                                                  records

  **Teammate 2**          Catalog, quotations,    Products, variants,
                          and subscriptions       plans, quotation
                                                  templates, quotation
                                                  workflow, subscription
                                                  lifecycle

  **Teammate 3**          Billing and invoice     Recurring billing,
                          engine                  invoice generation and
                                                  lifecycle, tax and
                                                  discount calculations

  **Teammate 4**          Payments, customer      Payment recording and
                          portal, and reporting   allocation,
                                                  customer-facing portal,
                                                  dashboard and reports,
                                                  notifications
  -----------------------------------------------------------------------

Each teammate is responsible for designing, implementing, testing, and
documenting their assigned workstream. Ownership does not mean working
in isolation: shared data contracts and integration points must be
agreed upon before implementation.

------------------------------------------------------------------------

# 2. Detailed work allocation

## Teammate 1 --- Identity, Access & Customer Foundation

### Objective

Build the account and customer foundation that the rest of Brightloop
relies on. Ensure users can securely access the platform and that each
role can access only the information and actions permitted to it.

### Responsibilities

**A. Authentication and account management** - User registration and
login. - Password validation according to the PRD. - Password hashing
and secure session handling. - Password-reset flow using expiring,
single-use reset tokens. - Unique and consistently normalized email
addresses. - Login throttling and account deactivation. - Link customer
portal accounts to the correct customer records.

**B. Role-based access control** - Define the roles: Administrator,
Operations Staff, Finance Staff, and Customer. - Define permissions for
each role. - Enforce permissions in the backend, not only in the
interface. - Ensure customers can access only their own records. -
Ensure only administrators can create staff accounts and manage discount
rules.

**C. Staff account management** - Administrator interface or workflow to
create staff accounts. - Assign and manage staff permissions. -
Deactivate staff access without deleting historical records.

**D. Customer management** - Create, view, update, search, and archive
customer records. - Support individual and business customers. - Store
contact details, billing address, optional tax identifier, payment
terms, and status. - Link a customer record to an optional portal
account. - Preserve historical financial records when customer details
change.

### Expected deliverables

-   Working login, logout, and password-reset workflows.
-   Role and permission model.
-   Staff account management.
-   Customer management screens and operations.
-   Backend access-control checks.
-   Tests for duplicate accounts, invalid passwords, unauthorized
    access, and customer data isolation.
-   A short document explaining the user roles, permissions, and
    customer data model.

### Integration responsibilities

-   Provide a stable user identity and customer identifier for other
    workstreams.
-   Agree with Teammate 4 on how customer portal users are linked to
    customer records.
-   Coordinate with Teammates 2 and 3 on which staff roles may perform
    their operations.

### Out of scope

-   Product and plan configuration.
-   Quotations and subscription lifecycle logic.
-   Invoice calculations and payment processing.
-   Financial dashboard calculations.

------------------------------------------------------------------------

## Teammate 2 --- Product Catalog, Quotations & Subscription Management

### Objective

Build the commercial workflow that turns a customer requirement into an
approved, active subscription.

### Responsibilities

**A. Product catalog** - Create, view, update, and archive products. -
Store product name, type, sales price, cost price, notes, and status. -
Support product variants and variant price adjustments. - Validate
product and variant selections. - Keep internal cost prices hidden from
customers. - Preserve historical references when products are archived
or prices change.

**B. Subscription plans** - Create and manage plans. - Support daily,
weekly, monthly, and yearly billing intervals. - Configure minimum
quantities and availability dates. - Configure whether a plan permits
pause, renewal, early closure, and automatic closure at expiry. - Store
payment terms and plan status. - Apply the agreed pricing interpretation
from the PRD.

**C. Quotation templates** - Create, edit, archive, and duplicate
templates. - Configure the applicable plan, product lines, quantities,
and validity duration. - Copy template values into a new quotation. -
Calculate quotation expiry. - Prevent expired quotations from being
confirmed unless extended or reissued.

**D. Quotation workflow** - Create quotations for customers. - Add
products, variants, quantities, and applicable pricing. - Validate
required fields and minimum quantities. - Support quotation review and
confirmation. - Preserve quotation details if the original template
changes.

**E. Subscription management** - Convert confirmed quotations into
subscriptions. - Store subscription number, customer, plan, start date,
expiry date, payment terms, and subscription lines. - Manage the
lifecycle: Draft → Quotation → Confirmed → Active → Closed. - Support
pause and resume where the plan permits it. - Support renewal by
creating a linked successor subscription. - Prevent closed or paused
subscriptions from generating new billing periods. - Preserve confirmed
commercial terms as a snapshot.

### Expected deliverables

-   Product and variant management.
-   Subscription plan management.
-   Quotation template management.
-   Quotation creation and confirmation workflow.
-   Subscription creation and lifecycle management.
-   Tests for pricing, quotation expiry, valid state transitions,
    pause/resume, renewal, and closure.
-   A short document explaining the subscription lifecycle and the data
    other modules need.

### Integration responsibilities

-   Provide the subscription identifier, status, billing interval,
    billing anchor, next billing date, customer, and billable line
    details to Teammate 3.
-   Coordinate with Teammate 1 for customer and staff identity
    references.
-   Coordinate with Teammate 4 so the customer portal can display
    subscription details and renewal information.

### Out of scope

-   Recurring invoice generation.
-   Invoice tax and discount calculations.
-   Payment recording and allocation.
-   Financial reporting.

------------------------------------------------------------------------

## Teammate 3 --- Recurring Billing, Invoices, Taxes & Discounts

### Objective

Build the financial engine that converts due subscriptions into accurate
invoices, while preventing duplicate billing and making failures
recoverable.

### Responsibilities

**A. Recurring billing engine** - Identify eligible active and running
subscriptions. - Determine the correct billing period for each
subscription. - Check whether an invoice already exists for that
subscription and period. - Generate invoices using subscription pricing
snapshots. - Advance billing checkpoints safely. - Process subscriptions
independently so one failure does not stop the entire billing batch. -
Support safe retries after failures or interruptions. - Recover missed
billing periods without silently combining them. - Prevent billing
beyond subscription expiry. - Ensure paused and closed subscriptions do
not generate new invoices.

**B. Invoice management** - Generate invoice numbers. - Store customer
and billing-address snapshots. - Store subscription reference and
service-period dates. - Store issue date, due date, line items, totals,
and outstanding balance. - Support Draft → Confirmed → Paid, with
cancellation and partial-payment indicators as defined in the PRD. -
Support confirmation, cancellation, sending, and printing. - Prevent
financial edits after confirmation. - Generate downloadable/printable
invoice documents. - Record invoice sending attempts and billing
failures.

**C. Tax calculation** - Configure and apply tax rules. - Support the
initial agreed tax scope: percentage-based, tax-exclusive rules. - Apply
applicable tax to invoice lines. - Use consistent monetary precision and
rounding. - Preserve tax details on confirmed invoices.

**D. Discount management** - Allow administrators to create and edit
discount rules. - Support fixed-amount and percentage discounts. -
Support minimum purchase or quantity, validity dates, usage limits, and
product-level or subscription-level application. - Apply eligible
discounts according to the PRD. - Prevent discounts from reducing an
eligible subtotal below zero. - Prevent parallel billing jobs from
exceeding discount usage limits. - Preserve discount details on
confirmed invoices.

**E. Billing operations visibility** - Record successful and failed
billing runs. - Expose affected subscriptions and useful error
details. - Provide a safe retry mechanism. - Ensure retries cannot
create duplicate invoices.

### Expected deliverables

-   Recurring billing workflow.
-   Invoice creation and management.
-   Tax and discount calculation logic.
-   Billing failure and retry handling.
-   Printable/downloadable invoice output.
-   Tests for duplicate prevention, retries, missed periods, expiry,
    tax, discounts, rounding, and invoice state changes.
-   A short document describing billing rules, calculation rules, and
    failure recovery.

### Integration responsibilities

-   Consume subscription and line-item information from Teammate 2.
-   Use customer and billing details provided by Teammate 1.
-   Provide invoice identifiers, totals, due dates, and outstanding
    balances to Teammate 4.
-   Coordinate with Teammate 4 on payment allocation and invoice balance
    updates.

### Out of scope

-   Creating or managing subscription plans and quotations.
-   Recording payments or reconciling bank statements.
-   Building the main financial dashboard.

------------------------------------------------------------------------

## Teammate 4 --- Payments, Customer Portal, Reporting & Notifications

### Objective

Complete the customer and finance-facing experience. Enable payment
tracking, customer visibility, and useful operational and financial
reporting.

### Responsibilities

**A. Payment recording** - Record payments with method, amount, date,
note, and invoice reference. - Support multiple payments against one
invoice. - Support partial payments. - Reject allocations exceeding the
outstanding invoice balance. - Store optional external payment
references. - Support audited payment reversals rather than permanent
deletion. - Recalculate invoice balances and payment status after
allocations or reversals.

**B. Customer portal** - Provide customers with access to their own
subscription information. - Show subscription status, plan, renewal
information, and relevant details. - Show invoices and allow customers
to download them. - Show recorded payments and outstanding balances. -
Allow permitted profile updates. - Allow customers to submit pause,
cancellation, or renewal requests. - Ensure customers cannot view or
modify another customer's records.

**C. Dashboard and reporting** - Show active and running subscription
counts. - Show billed amount and cash collected as separate metrics. -
Show outstanding balances and overdue invoices. - Provide filters for
date range, customer, plan, subscription status, invoice status, payment
method, and overdue condition. - Ensure dashboard totals reconcile with
invoice and payment records. - Make date-filter behavior clear (for
example, invoice issue date versus payment date).

**D. Notifications** - Coordinate password-reset and invoice email
integration with Teammate 1 and Teammate 3. - Support invoice delivery
and record sending outcomes. - Implement or prepare optional
notifications such as quotation emails, payment receipts, upcoming
expiry notices, and overdue reminders, subject to the agreed
initial-release scope.

### Expected deliverables

-   Payment recording and allocation workflow.
-   Partial-payment and reversal handling.
-   Customer portal.
-   Financial and subscription dashboard.
-   Report filters and summary views.
-   Notification workflows within the agreed scope.
-   Tests for payment allocation, overpayment prevention, reversals,
    customer data isolation, and report reconciliation.
-   A short document defining dashboard metrics and payment behavior.

### Integration responsibilities

-   Consume customer and access-control information from Teammate 1.
-   Consume subscription information from Teammate 2.
-   Consume invoice and balance information from Teammate 3.
-   Coordinate invoice balance and payment status updates with Teammate
    3.
-   Ensure customer-facing screens show only customer-authorized data.

### Out of scope

-   Subscription pricing and lifecycle management.
-   Recurring invoice generation.
-   Tax and discount rule calculation.
-   Full accounting or general-ledger functionality.
-   Automatic bank reconciliation or payment gateway integration unless
    separately approved.

------------------------------------------------------------------------

# 3. Shared integration contracts

The four workstreams depend on one another. Before building
independently, agree on the following shared records and operations.

  Shared item                            Primary owner   Used by
  -------------------------------------- --------------- -------------------------------
  User identity and role                 Teammate 1      All teammates
  Customer record and customer ID        Teammate 1      Teammates 2, 3, 4
  Product and variant details            Teammate 2      Teammates 3, 4
  Plan and billing interval              Teammate 2      Teammates 3, 4
  Quotation and confirmed subscription   Teammate 2      Teammates 3, 4
  Subscription billing details           Teammate 2      Teammate 3
  Tax and discount rules                 Teammate 3      Billing and invoice workflows
  Invoice and invoice balance            Teammate 3      Teammate 4
  Payment and allocation records         Teammate 4      Teammates 3, 4
  Dashboard metrics                      Teammate 4      Admin and finance users

### Required team agreements

Before implementation, the team must agree on: 1. Common naming for
shared entities and identifiers. 2. Required fields and allowed values
for shared records. 3. Subscription, invoice, and payment status
definitions. 4. Date, timezone, currency, and monetary precision
conventions. 5. How one workstream communicates changes to another. 6.
Which teammate owns each shared calculation or state transition. 7. How
authentication and permissions are checked by every module.

**Important:** Do not let two teammates independently implement
competing versions of the same business rule. For example, Teammate 3
owns invoice total calculation, while Teammate 4 owns payment
allocation. Teammate 4 should use the invoice balance contract rather
than create a separate invoice calculation.

------------------------------------------------------------------------

# 4. Suggested implementation sequence

The team can work in parallel after agreeing on shared contracts. The
following order identifies dependencies; it does not require everyone to
wait until the previous workstream is fully complete.

  -------------------------------------------------------------------------------
  Stage          Teammate 1       Teammate 2      Teammate 3       Teammate 4
  -------------- ---------------- --------------- ---------------- --------------
  **1. Define**  Roles, users,    Product, plan,  Invoice, tax,    Payment,
                 customer fields  quotation,      discount,        portal,
                                  subscription    billing rules    reporting
                                  rules                            rules

  **2. Build     Authentication   Product catalog Calculation      Portal layout
  foundation**   and customer     and plans       rules and        and reporting
                 records                          invoice          definitions
                                                  structure        

  **3. Build     Staff            Quotations and  Billing and      Payment
  workflows**    permissions and  subscription    invoice          recording and
                 customer         lifecycle       generation       allocation
                 operations                                        

  **4.           Connect access   Supply          Consume          Consume
  Integrate**    checks and       confirmed       subscriptions;   invoices;
                 customer records subscriptions   publish invoices update payment
                                                                   and portal
                                                                   views

  **5.           Security and     Lifecycle and   Billing accuracy Payment,
  Validate**     access tests     pricing tests   and retry tests  portal
                                                                   isolation, and
                                                                   report tests

  **6.           Fix integration  Fix integration Fix integration  Fix
  Finalize**     issues           issues          issues           integration
                                                                   issues
  -------------------------------------------------------------------------------

------------------------------------------------------------------------

# 5. Integration checkpoints

Use explicit checkpoints so that integration does not become a
last-minute activity.

### Checkpoint 1 --- Shared design agreed

-   All four teammates understand the PRD.
-   Ownership boundaries are accepted.
-   Shared entities and identifiers are agreed.
-   Each teammate has independently researched and selected a suitable
    technology approach.
-   Compatibility questions are resolved together.

### Checkpoint 2 --- Basic modules work independently

-   Each teammate can demonstrate their assigned module with sample
    data.
-   Each module has basic validation and error handling.
-   No teammate depends on undocumented assumptions from another module.

### Checkpoint 3 --- First end-to-end flow works

The team should demonstrate this complete journey:

1.  Create a customer.
2.  Configure a product and subscription plan.
3.  Create and confirm a quotation.
4.  Activate the subscription.
5.  Generate an invoice for a due billing period.
6.  Record a partial payment.
7.  Display the updated outstanding balance.
8.  Show the updated information in the dashboard and customer portal.

### Checkpoint 4 --- Reliability and final validation

-   Test role permissions and customer data isolation.
-   Test duplicate billing prevention.
-   Test partial payments and payment reversals.
-   Test tax and discount calculations.
-   Test pause, resume, renewal, and closure.
-   Test failed billing jobs and safe retries.
-   Verify that dashboard totals reconcile with underlying records.

------------------------------------------------------------------------

# 6. Individual definition of done

A workstream is not complete merely because its screens exist.

Every teammate must deliver:

-   [ ] A working implementation of the assigned responsibilities.
-   [ ] Clear validation and error handling.
-   [ ] Tests for the important business rules.
-   [ ] Sample data or a repeatable demonstration path.
-   [ ] Documentation of the module's behavior and assumptions.
-   [ ] A list of interfaces and dependencies required by other
    teammates.
-   [ ] A list of unfinished work and known limitations.
-   [ ] Successful integration with the relevant neighboring
    workstreams.

------------------------------------------------------------------------

# 7. Team-wide rules

1.  **Own your module end to end.** Do not leave core logic unfinished
    while polishing secondary screens.
2.  **Agree on contracts before integration.** Shared records, fields,
    statuses, and responsibilities must be clear.
3.  **Do not silently change another teammate's module.** Discuss
    changes to shared behavior first.
4.  **Keep business rules consistent.** One authoritative implementation
    should own each calculation and state transition.
5.  **Integrate continuously.** Do not wait until every module is
    complete before connecting them.
6.  **Test with realistic sample data.** Include normal, invalid,
    partial, expired, and failure scenarios.
7.  **Document assumptions.** If the PRD does not define a behavior,
    record the proposed decision and get team agreement.
8.  **Keep the first release within scope.** Do not add payment gateway
    integration, automatic bank reconciliation, or full accounting
    functionality unless the team explicitly approves the scope change.
9.  **Each teammate chooses and justifies their own technology
    decisions.** The final choices must be compatible across the
    complete system.
10. **Prioritize a complete end-to-end workflow.** A connected, reliable
    subscription-to-payment journey is more valuable than four
    disconnected modules.

------------------------------------------------------------------------

## Final ownership summary

-   **Teammate 1:** Who can access Brightloop, what they can do, and
    which customer records exist.
-   **Teammate 2:** What Brightloop sells, what customers are quoted,
    and how subscriptions are managed.
-   **Teammate 3:** When customers are billed, how invoices are
    calculated, and how billing failures are handled.
-   **Teammate 4:** How payments are recorded, what customers can see,
    and how the business monitors performance.

**The shared goal:** Deliver one connected Brightloop platform---not
four separate projects stitched together at the end.
