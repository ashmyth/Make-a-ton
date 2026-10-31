# Brightloop — Teammate 1: Complete Work Plan, Architecture & Implementation Guide

**Project:** Brightloop Subscription Management Platform  
**Owner:** Teammate 1 — Identity, Access & Customer Foundation  
**Architecture:** Django 5 Modular Monolith + DRF + PostgreSQL (Strictly aligned with [`TECK_STACK.md`](file:///d:/Make-a-ton/TECK_STACK.md) v2.0)  
**Reference Documents:** [`TECK_STACK.md`](file:///d:/Make-a-ton/TECK_STACK.md), [`work division.md`](file:///d:/Make-a-ton/work%20division.md), [`Brightloop PRD v1.0`](file:///d:/Make-a-ton/Brightloop_Subscription_Management_Platform_PRD.md)  
**Status:** Approved & Implemented

---

## 1. Executive Summary & Objective

As **Teammate 1**, you own the **Identity, Access & Customer Foundation** of the Brightloop platform. Every other domain relies on your models, permission enforcement, and authentication tokens:

- **Teammate 2 (Catalog & Subscriptions):** Links subscriptions to verified customers and audits staff ownership.
- **Teammate 3 (Billing Engine):** Requires customer billing address snapshots, tax IDs, and verifies staff finance permissions.
- **Teammate 4 (Payments, Portal & Reporting):** Relies on authenticated sessions, `request.user.customer_id`, customer isolation (anti-IDOR), and finance reporting RBAC.

> **Ownership Boundary:** You determine **who can access Brightloop**, **what actions their role permits**, and **which customer records exist**.

---

## 2. System Architecture & Topology (`TECK_STACK.md` §1)

Production runs **three processes** (Caddy reverse proxy, Django web process, and Procrastinate background worker) and **two stateful systems** (PostgreSQL and S3-compatible object storage):

```
Browser (React SPA, static files)
        │  same origin
Caddy reverse proxy ── /      → static SPA build
        │             └ /api  → Django 5 (gunicorn)
        ▼
Django + DRF (modular monolith)
        │                         │
        ▼                         ▼
PostgreSQL (all state)      Object storage (invoice PDFs)
   ▲
   │ jobs, locks, billing state, audit
Procrastinate worker (PDF, email, billing sweep)
```

---

## 3. Technology Stack Alignment with `TECK_STACK.md`

Your workstream strictly conforms to the choices justified in [`TECK_STACK.md`](file:///d:/Make-a-ton/TECK_STACK.md):

| Layer | Approved Technology | PRD Driver & Justification from `TECK_STACK.md` |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.12+ / Django 5 + Django REST Framework** | Modular monolith; robust financial logic, atomic DB writes, session auth. |
| **Domain App Boundaries** | **`identity` & `audit`** (enforced by `import-linter`) | Clear boundary ownership; encapsulates accounts, staff, customers, and RBAC. |
| **Primary Database** | **PostgreSQL (UUIDv4 + `citext`)** | Relational integrity, ACID transactions, `citext` for unique case-insensitive email (AUTH-01). |
| **Sessions & Cache** | **Django Database Sessions & DB Cache Backend** | AUTH-06, DRF throttling. **No Redis** needed; eliminates extra stateful dependencies (§2, §9). |
| **Authentication** | **Django Session Authentication (HttpOnly cookies)** | Secure financial app architecture; avoids XSS risks of JWT in localStorage (§9). |
| **Password Security** | **Argon2id (`argon2-cffi`)** | State-of-the-art password hashing (AUTH-02). |
| **Password Validator** | **Custom `BrightloopPasswordValidator`** | PRD §7.1 requirement: 9+ chars, uppercase, lowercase, special character. |
| **Brute-Force & Rate Limiting** | **`django-axes` / DB lockout tracker** | AUTH-06: 5 failed attempts locks account for 15 minutes; neutral reset response. |
| **Password Reset** | **Cryptographic random tokens (`secrets`)** | AUTH-03: Single-use, expiring, DB stores only SHA-256 hash. |
| **Email Delivery** | **`django-anymail` (SES / Postmark) + `EmailLog`** | Password reset emails enqueued via Procrastinate; logged in `EmailLog` table (§2). |
| **Role-Based Access Control** | **DRF Permission Classes** | Administrator, Operations Staff, Finance Staff, Customer; backend enforcement. |
| **Customer Data Isolation** | **Scoped QuerySets & `CustomerDataIsolation`** | Anti-IDOR: Customers only access their own records (`request.user.customer_id`). |
| **Audit Logging** | **`django-pghistory` / `brightloop_audit_logs`** | Trigger-based and service-layer immutable audit trail of all security and data events. |
| **API Schema & Docs** | **`drf-spectacular` (OpenAPI 3.0)** | Typed OpenAPI contract used to generate frontend client via Orval. |
| **Reverse Proxy** | **Caddy** | Same-origin serving (`/` to SPA, `/api` to Django); automatic TLS; eliminates CORS. |
| **Frontend Framework** | **Vite + React + strict TypeScript** | Fast, type-safe console and portal surfaces; no SSR needed. |
| **Frontend Routing** | **TanStack Router** | Typed routes and search params; separate lazy-loaded `/console` and `/portal` trees. |
| **Frontend State & Forms** | **TanStack Query, react-hook-form + zod** | Server state caching, client form validation matching backend rules. |
| **Frontend UI** | **Tailwind CSS + shadcn/ui (Radix)** | High-accessibility CRM tables, modal dialogs, and admin forms. |
| **Automated Testing** | **Pytest + pytest-django + factory_boy** | Unit, integration, security, and IDOR isolation test suites. |
| **Static Code Quality** | **Ruff, Mypy (strict with `django-stubs`), `import-linter`** | Clean code quality and modular architecture boundaries. |

---

## 4. Architecture & Domain Structure

In accordance with `TECK_STACK.md` Section 2, the application runs as a modular monolith. Teammate 1 provides the `identity` domain (structured into clean, focused apps) and the `audit` domain:

```
d:\Make-a-ton\backend\
├── brightloop/                 # Core Django project configuration
│   ├── settings.py             # PostgreSQL, DB sessions, DB cache, Argon2, DRF, Spectacular
│   ├── urls.py                 # Master API router (/api/v1/...)
│   └── wsgi.py / asgi.py
├── apps/
│   ├── accounts/               # User authentication & credentials
│   │   ├── models.py           # User model (UUID pk, citext email, Argon2, lockout fields)
│   │   ├── validators.py       # BrightloopPasswordValidator (9+ chars, A-Z, a-z, special)
│   │   ├── serializers.py      # Register, Login, Me, PasswordReset serializers
│   │   ├── views.py            # Login, Logout, Register, Me, Password Reset views
│   │   └── urls.py             # /api/v1/auth/
│   ├── access_control/         # RBAC & authorization guards
│   │   ├── roles.py            # UserRole (ADMINISTRATOR, OPERATIONS, FINANCE, CUSTOMER)
│   │   └── permissions.py      # IsAdministrator, IsOperationsStaff, IsFinanceStaff, CustomerDataIsolation
│   ├── staff/                  # Staff account lifecycle
│   │   ├── serializers.py      # Staff list, create, update serializers
│   │   ├── views.py            # Admin-only staff CRUD & soft deactivation
│   │   └── urls.py             # /api/v1/staff/
│   ├── customers/              # Customer CRM foundation
│   │   ├── models.py           # Customer model (UUID pk, code, business/individual, address, terms)
│   │   ├── serializers.py      # CustomerSerializer, LinkPortalUserSerializer
│   │   ├── views.py            # Customer CRUD, search/filter, soft archive, portal linking
│   │   └── urls.py             # /api/v1/customers/
│   └── audit/                  # Security & data event tracking
│       ├── models.py           # AuditLog model (actor, action, entity, details, IP, timestamp)
│       ├── services.py         # record_audit() helper
│       ├── views.py            # Admin audit log inspection endpoint
│       └── urls.py             # /api/v1/audit/
├── tests/                      # Pytest automated test suite
│   ├── test_auth.py            # Password rules, unique email, throttling, token reset
│   ├── test_rbac.py            # Role enforcement & customer data isolation (IDOR)
│   ├── test_staff.py           # Staff creation, soft deactivation, lockout
│   └── test_customers.py        # CRM creation, search, archiving, portal linking
├── requirements.txt            # Python dependencies (pinned to TECK_STACK.md specs)
├── pytest.ini                  # Pytest configuration
└── manage.py                   # Django CLI
```

---

## 5. Database Schema Specifications

### 5.1 `brightloop_users` (User Identity)
* `id`: `UUID` primary key (`default=uuid.uuid4`).
* `email`: `citext` / `EmailField(unique=True, db_index=True)` (normalized lowercase, trimmed).
* `password`: Argon2id hashed string (`argon2$argon2id$...`).
* `role`: Enum `['ADMINISTRATOR', 'OPERATIONS', 'FINANCE', 'CUSTOMER']`.
* `is_active`: `bool` (soft deactivation toggle; deactivating retains historical records).
* `failed_login_attempts`: `int` (incremented on failed password).
* `locked_until`: `timestamptz` (set to `now() + 15 min` after 5 failed attempts).
* Helper properties: `customer_id`, `customer`, `full_name`.

### 5.2 `brightloop_customers` (Customer CRM Record)
* `id`: `UUID` primary key (`default=uuid.uuid4`).
* `customer_code`: Unique system-generated code (e.g. `CUST-E0070020`).
* `customer_type`: `'INDIVIDUAL'` or `'BUSINESS'`.
* `display_name`: Company legal name or individual full name.
* `contact_person`, `email`, `phone`.
* `billing_street`, `billing_city`, `billing_state`, `billing_postal_code`, `billing_country`.
* `tax_identifier`: Optional VAT / GST / EIN.
* `payment_terms`: `'IMMEDIATE'`, `'NET_15'`, `'NET_30'`, `'NET_60'`.
* `status`: `'ACTIVE'` or `'ARCHIVED'` (soft deletion; cannot delete customers with financial history).
* `portal_user_id`: Foreign key (`OneToOneField`) to `brightloop_users(id)` for customer portal login.

### 5.3 `brightloop_password_reset_tokens`
* `id`: `UUID` primary key.
* `user_id`: Foreign key to `brightloop_users`.
* `token_hash`: SHA-256 hash of single-use URL token.
* `expires_at`: Expiry timestamp (30-minute validity window).
* `is_used`: `bool` (marked true on consumption).

### 5.4 `brightloop_audit_logs`
* `id`: `UUID` primary key.
* `actor_id`: Foreign key to `brightloop_users`.
* `action`: Action string (`'LOGIN_SUCCESS'`, `'LOGIN_FAILED'`, `'STAFF_DEACTIVATED'`, `'CUSTOMER_UPDATED'`).
* `entity_type` & `entity_id`: Target entity (e.g. `Customer`, `User`).
* `details`: `JSONB` diff / metadata.
* `ip_address`: Client IP address.
* `timestamp`: `timestamptz` (indexed, descending).

---

## 6. API Architecture (`/api/v1/`)

All APIs follow a clean, versioned REST pattern with drf-spectacular OpenAPI documentation:

| Module | Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `GET` | `/api/v1/auth/csrf/` | Public | Returns CSRF token for forms. |
| **Auth** | `POST` | `/api/v1/auth/register/` | Public | Registers a new Customer portal account. |
| **Auth** | `POST` | `/api/v1/auth/login/` | Public | Session login with rate limiting & lockout check. |
| **Auth** | `POST` | `/api/v1/auth/logout/` | Authenticated | Clears user session. |
| **Auth** | `GET` | `/api/v1/auth/me/` | Authenticated | Returns logged-in user profile & `customer_id`. |
| **Auth** | `POST` | `/api/v1/auth/password-reset/` | Public | Generates single-use token; returns neutral response. |
| **Auth** | `POST` | `/api/v1/auth/password-reset-confirm/` | Public | Validates token and applies 9+ char password rules. |
| **Staff** | `GET` | `/api/v1/staff/` | Administrator | Lists all staff accounts with roles and active status. |
| **Staff** | `POST` | `/api/v1/staff/` | Administrator | Creates an Operations or Finance staff account. |
| **Staff** | `PATCH` | `/api/v1/staff/{id}/` | Administrator | Updates staff roles or permissions. |
| **Staff** | `POST` | `/api/v1/staff/{id}/deactivate/` | Administrator | Soft-deactivates staff member without deleting history. |
| **Staff** | `POST` | `/api/v1/staff/{id}/activate/` | Administrator | Reactivates staff account. |
| **Customers** | `GET` | `/api/v1/customers/` | Staff (Admin/Ops/Fin)| Searchable (`?search=`), filterable (`?status=ACTIVE`). |
| **Customers** | `POST` | `/api/v1/customers/` | Ops Staff / Admin | Creates customer record and generates `CUST-XXXX` code. |
| **Customers** | `GET` | `/api/v1/customers/my-profile/`| Customer User | Returns authenticated customer's own profile. |
| **Customers** | `GET` | `/api/v1/customers/{id}/` | Staff / Owner | Retrieves customer details (guarded by data isolation).|
| **Customers** | `PATCH` | `/api/v1/customers/{id}/` | Staff / Owner | Updates customer details (customers limited to contact/address). |
| **Customers** | `POST` | `/api/v1/customers/{id}/archive/`| Ops Staff / Admin | Soft archives customer record. |
| **Customers** | `POST` | `/api/v1/customers/{id}/link-portal/`| Ops Staff / Admin | Connects customer record to a portal user login. |
| **Audit** | `GET` | `/api/v1/audit/` | Administrator | Lists audit logs with filter/search support. |
| **OpenAPI** | `GET` | `/api/docs/` | Public / Developers | Interactive Swagger UI. |

---

## 7. Shared Integration Contracts with Other Teammates

### What Teammates 2, 3, and 4 get from Teammate 1:

1. **`request.user.customer_id`:**
   Teammate 4 (Customer Portal) uses this property directly to scope subscriptions, invoices, and payments:
   ```python
   # Inside Teammate 4's view:
   customer_id = request.user.customer_id
   invoices = Invoice.objects.filter(customer_id=customer_id)
   ```
2. **`request.user.customer`:**
   Direct reference to the linked [`Customer`](file:///d:/Make-a-ton/backend/apps/customers/models.py) model instance.
3. **Reusable Permissions:**
   - `IsAdministrator`: Admin-only operations.
   - `IsOperationsStaff`: Commercial workflows (Teammate 2).
   - `IsFinanceStaff`: Invoicing and payments (Teammate 3 & 4).
   - `IsCustomerUser`: Customer portal boundary.
   - `CustomerDataIsolation`: Prevents IDOR vulnerabilities.
4. **Customer Snapshot Contract (Teammate 3):**
   When Teammate 3 issues a confirmed invoice, they copy the customer's billing address and tax ID as immutable snapshot columns, ensuring future edits to the customer CRM do not rewrite past invoices.

---

## 8. Architectural Tradeoffs & Rejected Alternatives (`TECK_STACK.md` §8 & §9)

Teammate 1's work explicitly respects the ADRs and rejected alternatives from the master stack:

| Alternative | Status | Reason Rejected in `TECK_STACK.md` |
| :--- | :--- | :--- |
| **Redis for Sessions & Rate Limits** | **Rejected** | Extra stateful system; PostgreSQL database sessions and DB cache backend are durable and sufficient at thousands-of-users scale. |
| **JWT in `localStorage`** | **Rejected** | XSS vulnerable; HttpOnly session cookies are strictly required for financial safety. |
| **Next.js / SSR** | **Rejected** | No public SEO need for an authenticated enterprise console; Vite + React SPA eliminates CORS/CSRF complexity. |
| **GraphQL** | **Rejected** | REST with OpenAPI 3.0 gives simpler permissions, typed clients via Orval, and predictable endpoint boundaries. |
| **Django Admin for Financials** | **Restricted** | Bypasses the service layer, validation, and immutability rules. |

---

## 9. Quality Assurance & Automated Test Suite

Running `pytest` executes **23 tests** verifying every requirement of PRD §7.1 and §7.2:

```
collected 23 items

tests/test_auth.py::TestPasswordValidation::test_password_too_short PASSED
tests/test_auth.py::TestPasswordValidation::test_password_missing_uppercase PASSED
tests/test_auth.py::TestPasswordValidation::test_password_missing_lowercase PASSED
tests/test_auth.py::TestPasswordValidation::test_password_missing_special PASSED
tests/test_auth.py::TestPasswordValidation::test_valid_password PASSED
tests/test_auth.py::TestUserRegistrationAndUniqueness::test_email_normalization PASSED
tests/test_auth.py::TestUserRegistrationAndUniqueness::test_duplicate_email_registration_rejected PASSED
tests/test_auth.py::TestLoginThrottlingAndLockout::test_login_throttling_after_consecutive_failures PASSED
tests/test_auth.py::TestPasswordResetFlow::test_password_reset_neutral_response PASSED
tests/test_auth.py::TestPasswordResetFlow::test_single_use_expiring_token PASSED
tests/test_customers.py::TestCustomerManagement::test_create_customer PASSED
tests/test_customers.py::TestCustomerManagement::test_search_customer PASSED
tests/test_customers.py::TestCustomerManagement::test_archive_customer PASSED
tests/test_customers.py::TestCustomerManagement::test_link_portal_user PASSED
tests/test_rbac.py::TestRoleBasedAccessControl::test_operations_cannot_create_staff_account PASSED
tests/test_rbac.py::TestRoleBasedAccessControl::test_admin_can_create_staff_account PASSED
tests/test_rbac.py::TestRoleBasedAccessControl::test_customer_cannot_access_staff_endpoints PASSED
tests/test_rbac.py::TestRoleBasedAccessControl::test_customer_cannot_view_other_customer_record PASSED
tests/test_rbac.py::TestRoleBasedAccessControl::test_customer_can_view_own_record PASSED
tests/test_rbac.py::TestRoleBasedAccessControl::test_customer_cannot_modify_forbidden_fields PASSED
tests/test_staff.py::TestStaffManagement::test_admin_can_deactivate_staff PASSED
tests/test_staff.py::TestStaffManagement::test_deactivated_staff_cannot_login PASSED
tests/test_staff.py::TestStaffManagement::test_admin_cannot_deactivate_self PASSED

============================= 23 passed in 3.40s ==============================
```

---

## 10. Seed Data for Immediate Demonstration

A management command is included to seed all roles and test accounts:
```bash
python manage.py seed_data
```

| Role | Email | Password | Linked Customer |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@brightloop.io` | `Admin@Brightloop123` | System Admin |
| **Operations Staff** | `ops@brightloop.io` | `Ops@Brightloop123` | Operations Console |
| **Finance Staff** | `finance@brightloop.io` | `Finance@Brightloop123` | Finance Console |
| **Customer User** | `alice@acmecorp.com` | `Alice@Acme123` | Acme Corporation (`CUST-E0070020`) |
