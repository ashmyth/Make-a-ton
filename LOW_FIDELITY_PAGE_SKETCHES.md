# Brightloop Platform: Low-Fidelity UI Wireframes & Page Matrix

This document provides:
1. **Implementation Status Matrix** showing what has been built vs. what pages are still left to be implemented.
2. **Low-Fidelity ASCII Wireframe Sketches** for every single page/view (both existing and planned) across the Brightloop Subscription Management Platform.

---

## Part 1: Page Status Summary (Built vs. Left to Build)

### 🟢 Built & Available in Codebase
| Page / View | Location | Features Implemented |
| :--- | :--- | :--- |
| **Login & Register Modal** | `frontend/src/components/LoginModal.tsx` & `frontend(teammate 1)` | Email/Password auth, Password Reset Request & Confirmation, Sign up, Session tokens |
| **Customer Portal: Overview** | `frontend/src/components/CustomerPortal.tsx` | Active subscriptions summary, outstanding balance alert, quick links, recent invoices |
| **Customer Portal: Subscriptions** | `frontend/src/components/CustomerPortal.tsx` | List plans, renewal date, status badges, action triggers for Pause / Cancel / Renew request |
| **Customer Portal: Invoices & Payments** | `frontend/src/components/CustomerPortal.tsx` | View invoices, download PDF, outstanding vs paid status, payment transaction records |
| **Customer Portal: Profile / Billing Edit** | `frontend/src/components/CustomerPortal.tsx` | Contact info, billing address updating |
| **Finance Console: Dashboard & Analytics** | `frontend/src/components/FinanceConsole.tsx` | MRR, ARR, active subscribers, total revenue, overdue amounts, date-range filtering |
| **Finance Console: Invoices Management** | `frontend/src/components/FinanceConsole.tsx` | Invoice list, status filters, "Record Payment" modal with idempotency key, balance tracking |
| **Finance Console: Payments & Reversals** | `frontend/src/components/FinanceConsole.tsx` | Payment transaction registry, reverse payment modal with audit reason |
| **Staff CRM: Customer Management** | `frontend(teammate 1)/src/components/customers/CustomerManagement.tsx` | Customer list, customer detail drawer, create customer, link portal account |
| **Staff & Role Management** | `frontend(teammate 1)/src/components/staff/StaffManagement.tsx` | List staff, invite/create staff, assign roles (Admin, Ops, Finance), deactivate |
| **Audit Trail Logs** | `frontend(teammate 1)/src/components/audit/AuditTrail.tsx` | Immutably tracked operations, timestamp, actor, entity change, IP/payload inspector |
| **HTML/PDF Invoice Print Template** | `backend/apps/billing/templates/billing/invoice_pdf.html` | Clean printable invoice layout with tax breakdown & customer info |

---

### 🔴 Left to Build (Missing / Incomplete Pages)
| Missing Page / View | PRD Reference | Target Audience | Priority | What Needs to be Done |
| :--- | :--- | :--- | :--- | :--- |
| **1. Product & Variant Catalog** | PRD §7.3 | Ops Staff, Admin | **CRITICAL (High)** | Catalog UI to create products, set base price, define attributes (e.g., Brand, Cloud Tier), and price adjustments. |
| **2. Pricing Plans & Recurring Rules** | PRD §7.4 | Ops Staff, Admin | **CRITICAL (High)** | Setup recurring billing intervals (Monthly, Yearly), trial days, grace periods, and auto-renew flags. |
| **3. Quotation Templates & Builder** | PRD §7.5 | Ops Staff, Admin | **CRITICAL (High)** | Template manager (default lines/terms) and quote creator/editor with line items and discounts. |
| **4. Quotation Review & Conversion** | PRD §7.5 | Staff / Customer | **HIGH** | Dedicated quote presentation view where staff or customer clicks "Confirm & Convert to Subscription". |
| **5. Operations Subscription Lifecycle Hub** | PRD §7.6 | Ops Staff, Admin | **HIGH** | Manage active subscriptions: manual pause, resume, cancel, trigger immediate renewal, upgrade/downgrade. |
| **6. Taxes & Discount Rules Configurator** | PRD §7.8 | Admin only | **MEDIUM** | Admin panel to configure percentage/flat tax rates and discount rules (promo codes, volume discounts). |
| **7. Billing Automation Queue / Failures** | PRD §7.7 & §10 | Finance / Ops Staff | **MEDIUM** | Screen to view scheduled batch runs, dunning attempts, failed recurring invoice generations, and retry controls. |

---

## Part 2: Low-Fidelity ASCII Wireframe Sketches

```
==================================================================================================
PAGE 01: AUTHENTICATION MODAL / PAGE (Login / Register / Password Reset)
Status: [🟢 BUILT] - frontend/src/components/LoginModal.tsx
==================================================================================================

+------------------------------------------------------------------------------------------------+
|                                      BRIGHTLOOP PLATFORM                                       |
|                                                                                                |
|                               +----------------------------------+                             |
|                               | [BL] Brightloop Secure Login     |                             |
|                               +----------------------------------+                             |
|                               |  [ Sign In ]  |  [ Register ]    |                             |
|                               +----------------------------------+                             |
|                               | Email Address                    |                             |
|                               | [ user@example.com             ] |                             |
|                               |                                  |                             |
|                               | Password                         |                             |
|                               | [ ******************          ] |                             |
|                               |                                  |                             |
|                               | [?] Forgot Password?             |                             |
|                               |                                  |                             |
|                               | [      Log In to Brightloop    ] |                             |
|                               +----------------------------------+                             |
|                                                                                                |
|                         (Mode: Reset Password sends expiring token link)                       |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 02: CUSTOMER PORTAL - OVERVIEW & DASHBOARD
Status: [🟢 BUILT] - frontend/src/components/CustomerPortal.tsx (Tab: Overview)
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Brightloop        [Portal View]  (Staff: Switch to Finance)           (User: Acme Corp) [v]|
+------------------------------------------------------------------------------------------------+
|  [ Overview ]  |  [ Subscriptions (2) ]  |  [ Invoices (4) ]  |  [ Payments ]  |  [ Profile ]  |
+------------------------------------------------------------------------------------------------+
|                                                                                                |
|  ! OUTSTANDING BALANCE ALERT: You have $450.00 due on Invoice #INV-2026-004.    [ Pay Now ]   |
|                                                                                                |
|  +-------------------------+  +-------------------------+  +--------------------------------+  |
|  | ACTIVE SUBSCRIPTIONS    |  | NEXT RENEWAL DATE       |  | OUTSTANDING INVOICES           |  |
|  |           2             |  |      Nov 15, 2026       |  |           1 Unpaid             |  |
|  +-------------------------+  +-------------------------+  +--------------------------------+  |
|                                                                                                |
|  ACTIVE SERVICES                                                                               |
|  +------------------------------------------------------------------------------------------+  |
|  | Cloud SaaS Enterprise   | $1,200.00 / month | Renews in 15 days   | [ ACTIVE ]  [Manage] |  |
|  | Additional Seats (x5)   | $250.00 / month   | Renews in 15 days   | [ ACTIVE ]  [Manage] |  |
|  +------------------------------------------------------------------------------------------+  |
|                                                                                                |
|  RECENT INVOICES                                                                               |
|  +------------------------------------------------------------------------------------------+  |
|  | INV-2026-004 | Oct 01, 2026 | Total: $1,450.00 | Balance: $450.00 | [PARTIAL] | [PDF v]  |  |
|  | INV-2026-003 | Sep 01, 2026 | Total: $1,450.00 | Balance: $0.00   | [ PAID  ] | [PDF v]  |  |
|  +------------------------------------------------------------------------------------------+  |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 03: CUSTOMER PORTAL - SUBSCRIPTION MANAGEMENT & LIFECYCLE REQUESTS
Status: [🟢 BUILT] - frontend/src/components/CustomerPortal.tsx (Tab: Subscriptions)
==================================================================================================

+------------------------------------------------------------------------------------------------+
|  [ Overview ]  |  [*Subscriptions (2)*]  |  [ Invoices ]  |  [ Payments ]  |  [ Profile ]      |
+------------------------------------------------------------------------------------------------+
|                                                                                                |
|  YOUR SUBSCRIPTIONS                                                                            |
|                                                                                                |
|  +------------------------------------------------------------------------------------------+  |
|  | Enterprise Pro Cloud Tier                                               Status: [ACTIVE] |  |
|  | Plan Code: PLAN-ENT-M  |  Billing Interval: Monthly  |  Current Period: Oct 01 - Nov 01  |  |
|  | Amount: $1,200.00 / cycle                                                                |  |
|  |                                                                                          |  |
|  | Action Requests:  [ || Request Pause ]   [ X Request Cancellation ]   [ O Request Renew ]|  |
|  +------------------------------------------------------------------------------------------+  |
|                                                                                                |
|  MODAL: "Submit Subscription Change Request"                                                   |
|  +-------------------------------------------------------------+                              |
|  | Action: [ Pause Subscription                           |v]  |                              |
|  | Reason / Note: [ Pausing for seasonal maintenance....    ]  |                              |
|  |                [ Submit Request ]      [ Cancel ]           |                              |
|  +-------------------------------------------------------------+                              |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 04: CUSTOMER PORTAL - PROFILE & BILLING ADDRESS
Status: [🟢 BUILT] - frontend/src/components/CustomerPortal.tsx (Tab: Profile)
==================================================================================================

+------------------------------------------------------------------------------------------------+
|  [ Overview ]  |  [ Subscriptions ]  |  [ Invoices ]  |  [ Payments ]  |  [*Profile*]          |
+------------------------------------------------------------------------------------------------+
|                                                                                                |
|  ACCOUNT & BILLING DETAILS                                                                     |
|                                                                                                |
|  Company Name: Acme Corporation                      Account Email: billing@acme.com           |
|                                                                                                |
|  Primary Contact Person:                             Phone Number:                             |
|  [ John Doe                                      ]   [ +1 (555) 019-2834                    ]  |
|                                                                                                |
|  Billing Street:                                     City / Postal Code:                       |
|  [ 100 Innovation Way                            ]   [ San Francisco      ] [ 94105         ]  |
|                                                                                                |
|  State / Province:                                   Country:                                  |
|  [ California                                    ]   [ United States                        ]  |
|                                                                                                |
|  Tax Identification (GST/VAT):                       Payment Terms:                            |
|  [ US-948201948                                  ]   Net 30 Days (Managed by Admin)            |
|                                                                                                |
|  [ Save Changes ]                                                                              |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 05: FINANCE CONSOLE - EXECUTIVE DASHBOARD & REVENUE METRICS
Status: [🟢 BUILT] - frontend/src/components/FinanceConsole.tsx (Top Dashboard Section)
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Brightloop Finance Console        Date Range: [2026-10-01] to [2026-10-31]  [ Filter ]    |
+------------------------------------------------------------------------------------------------+
|  +--------------------+  +--------------------+  +--------------------+  +-------------------+ |
|  | MRR                |  | ARR                |  | TOTAL COLLECTED    |  | OVERDUE BALANCE   | |
|  | $84,320.00         |  | $1,011,840.00      |  | $78,140.00         |  | $6,180.00 (7 inv) | |
|  | (+8.2% vs last mo) |  | (+14% YoY)         |  | 92.6% recovery     |  | Requires Dunning  | |
|  +--------------------+  +--------------------+  +--------------------+  +-------------------+ |
|                                                                                                |
|  REVENUE RECOVERY TREND (Interactive Chart)                                                    |
|  +-------------------------------------------------------------------------------------------+ |
|  | $100k|                                                    ...---* Total Billed            | |
|  |  $75k|                                          ...--***          Collected               | |
|  |  $50k|                              ...--***                                              | |
|  |  $25k|                    ...--***                                                        | |
|  |    $0+----------------------------------------------------------------------------------- | |
|  |      Oct 01       Oct 07         Oct 14          Oct 21          Oct 28                   | |
|  +-------------------------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 06: FINANCE CONSOLE - INVOICES LEDGER & RECORD PAYMENT MODAL
Status: [🟢 BUILT] - frontend/src/components/FinanceConsole.tsx (Tab: Invoices)
==================================================================================================

+------------------------------------------------------------------------------------------------+
|  [*Invoices Ledger*]  |  [ Payments & Audit ]                                                  |
+------------------------------------------------------------------------------------------------+
| Filter: [ All Statuses |v]  [ Search customer/ID... ]                       [+ Record Payment] |
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | INVOICE #    | CUSTOMER      | DUE DATE    | TOTAL      | OUTSTANDING | STATUS   | ACTION      | |
| +--------------+---------------+-------------+------------+-------------+----------+-------------+ |
| | INV-2026-089 | Nova Corp     | 2026-11-02  | $4,200.00  | $4,200.00   | [ISSUED] | [Record Pay]| |
| | INV-2026-088 | Bright Tech   | 2026-10-28  | $1,800.00  | $600.00     | [PARTIAL]| [Record Pay]| |
| | INV-2026-087 | Acme Labs     | 2026-10-15  | $2,400.00  | $2,400.00   | [OVERDUE]| [Send Reminder]|
| | INV-2026-086 | Apex Global   | 2026-10-10  | $950.00    | $0.00       | [PAID]   | [View PDF]  | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
|  MODAL: "Record Customer Payment"                                                              |
|  +---------------------------------------------------------------------------------------+     |
|  | Invoice: [ INV-2026-088 - Bright Tech (Balance: $600.00)                         |v]  |     |
|  | Amount to Record: [ $600.00         ]   Payment Method: [ Bank Wire / EFT         |v]  |     |
|  | External Reference #: [ WIRE-90823401                                             ]  |     |
|  | Notes: [ Received via Chase corporate clearing                                    ]  |     |
|  | Idempotency Key: [ pay-173037281-9f82a1 ] (Auto-generated to prevent duplicates)     |     |
|  |                                                                                       |     |
|  | [ Confirm & Post Payment ]                                          [ Cancel ]        |     |
|  +---------------------------------------------------------------------------------------+     |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 07: FINANCE CONSOLE - PAYMENTS REGISTRY & REVERSAL MODAL
Status: [🟢 BUILT] - frontend/src/components/FinanceConsole.tsx (Tab: Payments)
==================================================================================================

+------------------------------------------------------------------------------------------------+
|  [ Invoices Ledger ]  |  [*Payments & Audit*]                                                  |
+------------------------------------------------------------------------------------------------+
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | RECEIPT #   | INVOICE LINK  | CUSTOMER      | METHOD    | AMOUNT     | STATUS  | ACTION        | |
| +-------------+---------------+---------------+-----------+------------+---------+---------------+ |
| | PAY-00382   | INV-2026-086  | Apex Global   | Wire      | $950.00    | [CLEARED| [Reverse]     | |
| | PAY-00381   | INV-2026-088  | Bright Tech   | Credit    | $1,200.00  | [CLEARED| [Reverse]     | |
| | PAY-00380   | INV-2026-081  | Zenith Corp   | ACH       | $3,100.00  | [REVOKED| (Reversed)    | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
|  MODAL: "Reverse Recorded Payment (Audit Controlled)"                                          |
|  +---------------------------------------------------------------------------------------+     |
|  | Target Payment: PAY-00382 ($950.00 - Apex Global)                                     |     |
|  | Reason for Reversal: (Required for regulatory audit)                                  |     |
|  | [ Customer bounced check / wire chargeback notification received from bank          ]  |     |
|  |                                                                                       |     |
|  | [ Reverse Payment & Re-open Balance ]                                 [ Dismiss ]     |     |
|  +---------------------------------------------------------------------------------------+     |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 08: STAFF CRM - CUSTOMER DIRECTORY & DETAIL DRAWER
Status: [🟢 BUILT] - frontend(teammate 1)/src/components/customers/CustomerManagement.tsx
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Brightloop Operations        [Customers]   [Staff & Roles]   [Audit Logs]      (Admin) [v]|
+------------------------------------------------------------------------------------------------+
| Filter: [ Search by name or email...              ] [ Status: Active |v]    [+ Create Customer]|
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | ID      | COMPANY / NAME    | CONTACT PERSON | EMAIL            | STATUS   | ACTIONS       | |
| +---------+-------------------+----------------+------------------+----------+---------------+ |
| | CUST-01 | Acme Corporation  | John Doe       | j.doe@acme.com   | [ACTIVE] | [View Details]| |
| | CUST-02 | Bright Tech Inc   | Sarah Connor   | sconnor@bt.com   | [ACTIVE] | [View Details]| |
| | CUST-03 | Cyberdyne Systems | Miles Dyson    | mdyson@cyber.com | [ARCHIVED| [View Details]| |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
|  CUSTOMER PROFILE DRAWER (Opens on clicking "View Details")                                    |
|  +-------------------------------------------------------------------------------------------+ |
|  | Acme Corporation (CUST-01)                                                    [ Close X ]  | |
|  | Status: [ACTIVE]  |  Currency: USD  |  Terms: Net 30  |  Tax ID: US-92837194               | |
|  |                                                                                           | |
|  | Linked Portal Account:                                                                    | |
|  | [ user@acme.com ] [ Unlink ]  or  [ Link Portal User ]                                    | |
|  |                                                                                           | |
|  | Associated Records:                                                                       | |
|  | -> Active Subscriptions: 2  |  Quotations: 1 Draft  |  Total Unpaid Invoices: $450.00     | |
|  |                                                                                           | |
|  | [ Edit Information ]                 [ Create Quote ]                 [ Archive Customer] | |
|  +-------------------------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 09: STAFF & RBAC PERMISSION MANAGEMENT
Status: [🟢 BUILT] - frontend(teammate 1)/src/components/staff/StaffManagement.tsx
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [Customers]   [*Staff & Roles*]   [Audit Logs]                                                 |
+------------------------------------------------------------------------------------------------+
| Only Administrators can manage internal staff credentials and system access profiles.         |
|                                                                              [+ Invite Staff]  |
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | NAME            | EMAIL              | ASSIGNED ROLE       | STATUS   | ACTIONS            | |
| +-----------------+--------------------+---------------------+----------+--------------------+ |
| | Alice Vance     | alice@brightloop.io| [ADMINISTRATOR   |v]| [ACTIVE] | [Deactivate] [PW]  | |
| | Bob Miller      | bob@brightloop.io  | [OPERATIONS      |v]| [ACTIVE] | [Deactivate] [PW]  | |
| | Carol Danvers   | carol@brightloop.io| [FINANCE         |v]| [ACTIVE] | [Deactivate] [PW]  | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
|  MODAL: "Add Staff Member"                                                                     |
|  +---------------------------------------------------------------------------------------+     |
|  | Full Name: [ Dave Bowman                          ] Email: [ dave@brightloop.io     ] |     |
|  | System Role: (o) Administrator   ( ) Operations Staff   ( ) Finance Staff             |     |
|  | Temporary Password: [ ******************          ]                                   |     |
|  | [ Create Staff Account ]                                              [ Cancel ]      |     |
|  +---------------------------------------------------------------------------------------+     |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 10: AUDIT TRAIL & SYSTEM LOGS (Immutable Security Logs)
Status: [🟢 BUILT] - frontend(teammate 1)/src/components/audit/AuditTrail.tsx
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [Customers]   [Staff & Roles]   [*Audit Logs*]                                                 |
+------------------------------------------------------------------------------------------------+
| Action Filter: [ All Actions |v]   Entity: [ All Entities |v]   Date: [ Past 7 Days |v]        |
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | TIMESTAMP       | ACTOR               | ACTION        | TARGET ENTITY | IP / PAYLOAD       | |
| +-----------------+---------------------+---------------+---------------+--------------------+ |
| | Oct 31 12:14:02 | carol@brightloop.io | PAYMENT_RECORD| PAY-00382     | [Inspect Diff]     | |
| | Oct 31 11:45:10 | bob@brightloop.io   | SUB_PAUSE_REQ | SUB-9021      | [Inspect Diff]     | |
| | Oct 31 09:30:22 | alice@brightloop.io | ROLE_MODIFIED | bob@brightloop| [Inspect Diff]     | |
| +--------------------------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------------------------+
```

---

## Part 3: Low-Fidelity Wireframes of the Pages LEFT TO BUILD

```
==================================================================================================
PAGE 11: PRODUCT & VARIANT CATALOG MANAGER
Status: [🔴 LEFT TO BUILD] - PRD §7.3
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Catalog & Plans        [Products & Variants]   [Plans]   [Taxes & Discounts]   (Ops) [v]  |
+------------------------------------------------------------------------------------------------+
| Filter: [ Search products...            ] [ Type: All |v]                   [+ New Product]    |
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | PRODUCT NAME        | TYPE      | BASE PRICE | COST PRICE | VARIANTS CONFIGURED | STATUS   | |
| +---------------------+-----------+------------+------------+---------------------+----------+ |
| | Cloud CRM Enterprise| Service   | $800.00    | $200.00    | Brand: Odoo (+$560) | [ACTIVE] | |
| | Dedicated Database  | Hardware  | $350.00    | $120.00    | Storage: 1TB (+$90) | [ACTIVE] | |
| | Support SLA Gold    | Support   | $150.00    | $30.00     | Tier: 24/7 (+$100)  | [ACTIVE] | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
|  DRAWER / MODAL: "Configure Product & Variants"                                                |
|  +-------------------------------------------------------------------------------------------+ |
|  | Product Name: [ Cloud CRM Enterprise           ]   Category: [ Software Services      |v] | |
|  | Base Sales Price: [ $800.00   ]                    Internal Cost: [ $200.00             ] | |
|  | Description / Notes: [ Full SaaS instance deployment with SSO and daily backup.         ] | |
|  |                                                                                           | |
|  | Variant Price Adjustments:                                                                | |
|  | +---------------------------------------------------------------------------------------+ | |
|  | | Attribute: [ Brand     ] Value: [ Odoo       ] Adjustment: [ +$560.00 ] [ Trash ]     | | |
|  | | Attribute: [ Storage   ] Value: [ 500GB SSD  ] Adjustment: [ +$50.00  ] [ Trash ]     | | |
|  | +---------------------------------------------------------------------------------------+ | |
|  | [+ Add Variant Option]                                                                    | |
|  |                                                                                           | |
|  | [ Save Product & Variants ]                                           [ Cancel ]          | |
|  +-------------------------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 12: SUBSCRIPTION PRICING PLANS & BILLING CYCLES
Status: [🔴 LEFT TO BUILD] - PRD §7.4
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [Products & Variants]   [*Plans*]   [Taxes & Discounts]                                        |
+------------------------------------------------------------------------------------------------+
| Define recurring cadence, grace periods, and auto-renewal policies.          [+ Create Plan]   |
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | PLAN CODE   | PLAN NAME            | INTERVAL | TRIAL DAYS | GRACE PERIOD | AUTO-RENEW     | |
| +-------------+----------------------+----------+------------+--------------+----------------+ |
| | PLAN-MO     | Standard Monthly     | Monthly  | 14 Days    | 5 Days       | Enabled        | |
| | PLAN-YR     | Annual Saver (15% off| Annual   | 0 Days     | 10 Days      | Enabled        | |
| | PLAN-QTR    | Corporate Quarterly  | 3 Months | 7 Days     | 7 Days       | Optional       | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
|  MODAL: "New Subscription Plan"                                                                |
|  +---------------------------------------------------------------------------------------+     |
|  | Plan Code: [ PLAN-SEMI-ANNUAL      ] Name: [ Semi-Annual Business Pro               ] |     |
|  | Billing Cadence: (o) Monthly   ( ) Quarterly   ( ) Semi-Annual   ( ) Annual           |     |
|  | Trial Period (Days): [ 14    ]   Invoice Due Offset: [ Net 15 Days                 |v]|     |
|  | Grace Period Before Suspension: [ 7 Days ]                                            |     |
|  | [X] Enforce Auto-Renewal by Default                                                   |     |
|  |                                                                                       |     |
|  | [ Save Plan Configuration ]                                           [ Cancel ]      |     |
|  +---------------------------------------------------------------------------------------+     |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 13: QUOTATION TEMPLATES & INTERACTIVE QUOTE BUILDER
Status: [🔴 LEFT TO BUILD] - PRD §7.5
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Sales Quotations              [Active Quotes]   [Templates]                     (Ops) [v] |
+------------------------------------------------------------------------------------------------+
| Quote ID: [ QUOTE-2026-012 ]          Customer: [ Acme Corporation                         |v] |
| Template: [ Enterprise Standard Cloud Package                                              |v] |
| Expiration Date: [ 2026-11-30 ]       Assigned Agent: [ Bob Miller (Operations)            |v] |
|                                                                                                |
| LINE ITEMS & PRODUCTS                                                                          |
| +--------------------------------------------------------------------------------------------+ |
| | ITEM / PRODUCT        | VARIANT         | QTY  | UNIT PRICE | DISCOUNT % | LINE TOTAL      | |
| +-----------------------+-----------------+------+------------+------------+-----------------+ |
| | Cloud CRM Enterprise  | Brand: Odoo     | 1    | $1,360.00  | 0.0%       | $1,360.00 [x]   | |
| | Dedicated Database    | Storage: 1TB    | 1    | $440.00    | 10.0%      | $396.00   [x]   | |
| +--------------------------------------------------------------------------------------------+ |
| [+ Add Product Line Item]                                                                      |
|                                                                                                |
| Applicable Tax Rule: [ Standard US Sales Tax (8.25%)                                       |v] |
|                                                                                                |
| FINANCIAL SUMMARY:                                                                             |
|   Subtotal:              $1,756.00                                                             |
|   Discount Applied:        -$44.00                                                             |
|   Tax (8.25%):            +$141.24                                                             |
|   Total Proposed:        $1,853.24 / month                                                     |
|                                                                                                |
| [ Save Draft ]         [ Generate Quote PDF ]         [ Send to Customer ]       [ Convert ]   |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 14: QUOTATION REVIEW & CONVERT-TO-SUBSCRIPTION WORKFLOW
Status: [🔴 LEFT TO BUILD] - PRD §7.5 & §7.6
==================================================================================================

+------------------------------------------------------------------------------------------------+
|  QUOTATION: QUOTE-2026-012  (Customer: Acme Corporation)                    Status: [APPROVED] |
+------------------------------------------------------------------------------------------------+
|                                                                                                |
|  Customer Signature / Approval: [ Signed by John Doe (j.doe@acme.com) on Oct 30, 2026 ]        |
|                                                                                                |
|  SUBSCRIPTION ACTIVATION PARAMETERS:                                                           |
|  +------------------------------------------------------------------------------------------+  |
|  | Start Date:             [ 2026-11-01 (Immediate)                                       ] |  |
|  | Billing Plan:           [ Standard Monthly (PLAN-MO)                                 |v] |  |
|  | First Invoice Action:   (o) Generate Invoice Immediately   ( ) Bill on Nov 01 Cycle      |  |
|  | Payment Terms:          [ Net 30 Days                                                |v] |  |
|  +------------------------------------------------------------------------------------------+  |
|                                                                                                |
|  WARNING: Converting this quotation will lock quotation line prices, activate recurring        |
|  billing schedules, and generate customer subscription SUB-9082.                               |
|                                                                                                |
|  [ -> CONFIRM & ACTIVATE SUBSCRIPTION <- ]                         [ Reject / Revise Quote ]   |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 15: OPERATIONS SUBSCRIPTION LIFECYCLE MANAGEMENT HUB
Status: [🔴 LEFT TO BUILD] - PRD §7.6
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Operations             [Subscriptions]   [Dunning & Billing Queue]              (Ops) [v] |
+------------------------------------------------------------------------------------------------+
| Filter: [ State: All |v]   [ Search Subscription or Customer...          ]                     |
|                                                                                                |
| +--------------------------------------------------------------------------------------------+ |
| | SUB ID   | CUSTOMER         | PLAN     | CURRENT CYCLE      | STATUS    | OPERATIONS       | |
| +----------+------------------+----------+--------------------+-----------+------------------+ |
| | SUB-1001 | Acme Corporation | Monthly  | Oct 01 - Nov 01    | [ACTIVE]  | [Manage v]       | |
| | SUB-1002 | Bright Tech Inc  | Annual   | Jan 01 - Dec 31    | [PAUSED]  | [Manage v]       | |
| | SUB-1003 | Cyberdyne Sys    | Monthly  | Sep 01 - Oct 01    | [SUSPEND] | [Manage v]       | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
|  MANAGE POPUP / MODAL for [SUB-1001]:                                                          |
|  +------------------------------------------------------------------------------------------+  |
|  | Manage Subscription #SUB-1001                                                            |  |
|  |                                                                                          |  |
|  |  ( ) Pause Subscription: Hold billing cycle for [ 30  ] days.                            |  |
|  |  ( ) Resume Subscription: Re-enable cycle and schedule next invoice.                      |  |
|  |  ( ) Renew Subscription: Extend cycle by 1 interval.                                     |  |
|  |  ( ) Trigger Manual Invoice: Generate next bill immediately.                              |  |
|  |  ( ) Terminate / Cancel: Close subscription at period end or immediately.                |  |
|  |                                                                                          |  |
|  | Reason for action: [ Customer requested temporary pause for winter maintenance ]         |  |
|  |                                                                                          |  |
|  | [ Execute Lifecycle Change ]                                           [ Dismiss ]       |  |
|  +------------------------------------------------------------------------------------------+  |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 16: TAX & DISCOUNT RULES ENGINE CONFIGURATOR
Status: [🔴 LEFT TO BUILD] - PRD §7.8
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Settings               [Tax Rules]   [Discount Codes & Promotions]            (Admin) [v] |
+------------------------------------------------------------------------------------------------+
| Manage statutory taxes and promotional/volume discount policies.            [+ Add Tax Rule]   |
|                                                                                                |
| TAX RULES REGISTRY                                                                             |
| +--------------------------------------------------------------------------------------------+ |
| | TAX NAME            | JURISDICTION | RATE % | COMPOUND | APPLIES TO            | STATUS    | |
| +---------------------+--------------+--------+----------+-----------------------+-----------+ |
| | California State Tax| US - CA      | 8.25%  | No       | All Products          | [ACTIVE]  | |
| | EU Standard VAT     | European Un. | 20.00% | No       | Digital Services      | [ACTIVE]  | |
| | GST India           | India        | 18.00% | No       | SaaS Software         | [ACTIVE]  | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
| DISCOUNT RULES & COUPONS                                                     [+ Add Discount]  |
| +--------------------------------------------------------------------------------------------+ |
| | CODE / NAME         | TYPE       | VALUE   | CRITERIA           | EXPIRY       | STATUS    | |
| +---------------------+------------+---------+--------------------+--------------+-----------+ |
| | EARLYBIRD10         | Percentage | 10.0%   | First 3 Cycles     | 2026-12-31   | [ACTIVE]  | |
| | CORP_SCALE_500      | Fixed      | $500.00 | Total > $5,000.00  | Ongoing      | [ACTIVE]  | |
| +--------------------------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------------------------+
```

```
==================================================================================================
PAGE 17: BILLING AUTOMATION ENGINE, DUNNING & RECOVERY QUEUE
Status: [🔴 LEFT TO BUILD] - PRD §7.7, §7.9, §10
==================================================================================================

+------------------------------------------------------------------------------------------------+
| [BL] Billing Engine         [Batch Automation]   [Failed Charges & Dunning]      (Finance) [v] |
+------------------------------------------------------------------------------------------------+
| Automated cron runs generate recurring invoices and track dunning retries. [ Run Manual Batch]|
|                                                                                                |
| SCHEDULED RECURRING BILLING JOBS                                                               |
| +--------------------------------------------------------------------------------------------+ |
| | BATCH ID   | RUN TIMESTAMP     | PROCESSED | INVOICES CREATED | FAILURES | STATUS          | |
| +------------+-------------------+-----------+------------------+----------+-----------------+ |
| | BAT-202610 | 2026-10-31 00:00  | 420 Subs  | 418 Invoices     | 2 Errors | [COMPLETED]     | |
| | BAT-202609 | 2026-09-30 00:00  | 395 Subs  | 395 Invoices     | 0 Errors | [COMPLETED]     | |
| +--------------------------------------------------------------------------------------------+ |
|                                                                                                |
| UNTRACKED / FAILED BILLING QUEUE (Action Required)                                             |
| +--------------------------------------------------------------------------------------------+ |
| | SUB ID   | CUSTOMER         | ATTEMPT | ERROR REASON                   | ACTION            | |
| +----------+------------------+---------+--------------------------------+-------------------+ |
| | SUB-1082 | Global Logistics | 2 of 3  | Missing tax snapshot / ID      | [Fix & Regenerate]| |
| | SUB-1140 | Helios Solar     | 1 of 3  | Customer archived with active  | [Review Account]  | |
| +--------------------------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------------------------+
```

---

## Part 4: Implementation Checklist & Next Steps

To complete the full Brightloop platform vision defined in `Brightloop_Subscription_Management_Platform_PRD.md` and `work division.md`:

- [x] **Teammate 1 (Identity & Customers):** Auth modal, Staff CRUD, Customer list/drawer, Audit logs (`frontend(teammate 1)`).
- [ ] **Teammate 2 (Catalog, Quotes & Subscriptions):** Wire up **Page 11 (Catalog)**, **Page 12 (Plans)**, **Page 13 (Quote Builder)**, **Page 14 (Quote Review)**, and **Page 15 (Subscription Lifecycle Hub)**.
- [ ] **Teammate 3 (Billing Engine):** Wire up **Page 16 (Tax & Discounts)** and **Page 17 (Billing Automation & Failures Queue)**.
- [x] **Teammate 4 (Payments, Portal & Finance):** Customer Portal (Pages 02-04), Finance Dashboard & Ledgers (Pages 05-07), Printable Invoices.

