# Brightloop — Module 2: Catalog, Quotations & Subscription Management
## Subscription Lifecycle & Integration Contracts Specification

**Author:** Teammate 2  
**Domain Apps:** `apps.catalog`, `apps.subscriptions`  
**Backend Framework:** Python 5 + Django REST Framework (Modular Monolith)  
**Database:** PostgreSQL  

---

## 1. Overview & Workstream Scope

Teammate 2 owns the commercial foundation of Brightloop:
* **Product Catalog:** Products and variants with positive/negative adjustments, soft-archiving, and cost-price privacy.
* **Subscription Plans:** Billing intervals (daily, weekly, monthly, yearly), minimum quantities, availability windows, and policy flags (`allow_pause`, `allow_early_closure`, `allow_renewal`, `auto_close_at_expiry`).
* **Quotation Templates:** Pre-configured plan and line defaults with deep cloning (`.duplicate()`).
* **Quotation Workflow:** Customer quotes, dynamic expiry calculation ($\text{issue\_date} + \text{validity\_days}$), commercial pricing snapshots, expiry extension, and confirmation guards.
* **Subscription Management:** Converting confirmed quotes into live subscriptions, operational pause/resume, renewals via linked successors, closures, and the recurring billing export feed.

---

## 2. Subscription Lifecycle State Machine

```
              ┌─────────┐
              │  Draft  │
              └────┬────┘
                   │ create quote
                   ▼
             ┌───────────┐
             │ Quotation │ ──(extend if expired)──> [ Reviewed ]
             └─────┬─────┘                               │
                   │ confirm                             │
                   ▼                                     │
            ┌─────────────┐ <────────────────────────────┘
            │  Confirmed  │
            └──────┬──────┘
                   │ convert to subscription
                   ▼
            ┌─────────────┐
            │   Active    │ <──────────┐
            │  (Running)  │            │
            └──────┬──────┘            │ resume
         pause │   │ renew             │
               │   │ (creates successor)
               ▼   ▼                   │
       ┌──────────────┐                │
       │    Active    │ ───────────────┘
       │   (Paused)   │
       └──────┬───────┘
              │ early close or term expiry
              ▼
       ┌──────────────┐
       │    Closed    │
       └──────────────┘
```

### Lifecycle Transition Rules:
1. **Draft $\rightarrow$ Quotation:** Initial quote created with billable products and plan.
2. **Quotation $\rightarrow$ Confirmed:** Validated that primary quantities meet `plan.min_quantity`. **Strict Guard:** If `today > expiry_date`, confirmation is blocked (HTTP 400) until an authorized user calls `POST /extend/`.
3. **Confirmed $\rightarrow$ Active Subscription:** `POST /convert-to-subscription/` generates `SUB-YYYY-NNNN`, initial billing anchor, and freezes commercial snapshot lines.
4. **Active (Running) $\rightarrow$ Active (Paused):** `POST /subscriptions/{id}/pause/`. **Strict Policy Check:** Only permitted if `plan.allow_pause == True`.
5. **Active (Paused) $\rightarrow$ Active (Running):** `POST /subscriptions/{id}/resume/`.
6. **Renewal:** `POST /subscriptions/{id}/renew/`. **Strict Policy Check:** Only permitted if `plan.allow_renewal == True`. Creates a linked successor subscription (`predecessor_id` $\leftrightarrow$ `successor_id`) and closes predecessor.
7. **Closure:** `POST /subscriptions/{id}/close/`. Permitted at term expiry or early cancellation if `plan.allow_early_closure == True`.

---

## 3. Shared Integration Contracts

### Contract 1: Teammate 3 (Recurring Billing Engine)

Teammate 3 queries due subscriptions to generate invoices. Teammate 2 exposes:

* **Endpoint:** `GET /api/subscriptions/due-for-billing/?as_of=YYYY-MM-DD`
* **Eligibility Filter (Zero Duplicate / Safe Billing):**
  * `status == "active"`
  * `operational_status == "running"`
  * `start_date <= as_of_date`
  * `next_billing_date <= as_of_date`
  * **Strict exclusion:** Paused and Closed subscriptions are **never** returned for billing.

#### Response Payload Schema (`SubscriptionBillingExport`):
```json
[
  {
    "subscription_id": "37ad74a5-4b6f-4dda-aeeb-73f721ee29a2",
    "subscription_number": "SUB-2026-0001",
    "customer_id": "CUST-1001",
    "plan_id": "b18b4562-7fa3-4355-83f5-7ee429d44f6d",
    "status": "active",
    "operational_status": "running",
    "billing_anchor_date": "2026-10-01",
    "next_billing_date": "2026-11-01",
    "billing_interval": "monthly",
    "start_date": "2026-10-01",
    "expiry_date": "2027-10-01",
    "payment_terms": "Net 30",
    "lines": [
      {
        "subscription_line_id": "a92e106e-821e-450f-90e2-ccbe19ec9137",
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "variant_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "description": "Enterprise ERP (Brand: Odoo)",
        "quantity": 5,
        "unit_price": "1560.00",
        "is_primary": true
      }
    ]
  }
]
```

---

### Contract 2: Teammate 4 (Customer Portal)

Teammate 4 consumes customer-facing subscription data:

* **Endpoint:** `GET /api/subscriptions/{id}/?view_as=customer` or `GET /api/subscriptions/?customer_id={id}&view_as=customer`
* **Security Rule:** Internal `cost_price` is stripped; shows renewal links (`successor_id`), plan name, interval, and payment terms.

---

### Contract 3: Teammate 1 (Identity & Customers)

* Teammate 2 consumes `customer_id` from Teammate 1.
* Audit and confirmation actions record `confirmed_by` staff identifiers.

---

## 4. PRD §7.4 Commercial Pricing Decision

Subscription line unit prices are the single source of recurring charges:
1. If a line is marked `is_primary == True` and the plan specifies `default_primary_unit_price`, that replaces the product base sales price.
2. Variant price adjustments are added to the base price ($1,000 + 560 = \$1,560$).
3. Add-on lines use their respective catalog sales prices + variant adjustments.
4. Plan price is not added again as a separate fee.
5. All prices freeze into permanent snapshots when quotations and subscriptions are created.

