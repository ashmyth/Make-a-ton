# Brightloop Unified Frontend — Impeccable Design Brief

## 1. Feature & Scope
- **Scope:** Full Frontend Redesign & Implementation of all 38 views (Auth, Staff Console, Customer Portal).
- **Architecture:** Single-App Architecture with Top Nav Switcher + Staff Sidebar Navigation, role-scoped by `/me` session.
- **Fidelity & Bar:** Production-ready code, live backend API integrations, real financial precision, zero fake or placeholder copy.

## 2. Visual Direction & Style Contract (From DESIGN.md)
- **Aesthetic:** Editorial Tech Journal on Warm Parchment (Monad / Stripe / Linear).
- **Canvas:** Warm Parchment (`#f6f3f1`), Off-Black (`#242424`) text, Ash (`#cecac8`) hairline borders, Periwinkle Mist (`#cfdaf5`) elevated cards.
- **Accent:** Lake Blue (`#2b59d1`) reserved strictly for the single primary conversion or confirmation action.
- **Typography:**
  - Headlines & Section Titles: **Untitled Serif** (or Georgia/Times fallback) at weight 400 only (no bold serifs).
  - Body, Navigation, Buttons, Tables, Data: **ABC Diatype Mono** (or JetBrains/Space Mono fallback) at 12–16px.
- **Affordances:**
  - 100px / 9999px pill buttons and badges.
  - 40px radius cards with 1px Ash borders (no drop shadows).
  - Scaled-down muted decimals on all monetary figures (e.g., `$1,200`.`00`).

## 3. Implementation Passes (Incremental Modular Delivery)
- **Pass 1: Foundations & Shell**
  - Theme CSS tokens, typography, root layout, and unified Top Navigation + Console Sidebar.
- **Pass 2: Auth Flow & Modals**
  - Login, Register (with 4 live password checklist checks), Forgot Password, and Reset Token.
- **Pass 3: Customer Portal (7 views)**
  - Overview, Subscriptions list + Lifecycle request modal, Invoices ledger + PDF download, Payments history, Profile editor.
- **Pass 4: Console Sales & CRM Module**
  - Customers directory & drawer, Products catalog & variant pricing, Plans, Quotations & interactive Quote Builder with backend validation.
- **Pass 5: Console Billing, Failures & Administration Module**
  - Invoices ledger + Record payment modal (idempotency key), Payments ledger + Audited reversal modal, Billing failures queue & retry runs, Staff management & RBAC, Immutable Audit Trail viewer.

