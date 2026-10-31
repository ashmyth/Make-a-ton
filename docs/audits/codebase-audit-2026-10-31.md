# Brightloop Adversarial Audit Report

**Date:** 2026-10-31  
**Auditor:** Teammate 4 (Autonomous Adversarial Security & Quality Review)  
**Target:** Entire Repository (`Make-a-ton`)  
**Scope:** Architecture, Security Boundaries, Financial Invariants, Data Isolation, PRD Alignment  
**Methodology:** Defect & Drift Hunting, Attack Surface Enumeration, Invariant Verification  

---

## 1. Executive Summary

This adversarial audit evaluates Brightloop against its Product Requirement Document (PRD v1.0), Technical Architecture specifications, and OWASP security standards. Rather than validating happy paths, this audit was conducted by probing for failure conditions, state desynchronization, credential exposures, injection vulnerabilities, and broken contracts between modules.

### Status Matrix

| ID | Category | Severity | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Security | **High** | Stored XSS in Invoice HTML Download (`PortalInvoiceDownloadView`) | Confirmed & Remediated |
| **SEC-02** | Security | **Medium** | Insecure CORS Wildcard with Credentials & Open `ALLOWED_HOSTS` | Confirmed & Remediated |
| **SEC-03** | Security | **Medium** | Insecure Hardcoded Fallback Secret Key | Confirmed & Remediated |
| **GAP-01** | PRD Compliance | **High** | Missing Append-Only Audit Logging on Financial & Identity Actions | Confirmed & Remediated |
| **GAP-02** | Architecture | **Medium** | Missing API Mounts for Audit, Staff, and Billing V1 Routes | Confirmed & Remediated |
| **HARD-01** | Hygiene | **Medium** | Demo Shortcuts & Hardcoded Plaintext Passwords in Login Modal | Confirmed & Remediated |
| **HARD-02** | Hygiene | **Low** | Redundant Duplicate Configuration Block in Django Settings | Confirmed & Remediated |

---

## 2. In-Depth Findings & Vulnerability Analysis

### SEC-01: Stored Cross-Site Scripting (XSS) in Invoice HTML Download
- **Affected File:** `backend/apps/portal/views.py` (`PortalInvoiceDownloadView`)
- **Severity:** High
- **Attack Vector:**
  1. A customer authenticates to the Customer Portal.
  2. The customer issues a `PATCH /api/v1/portal/profile/` containing a malicious string in `display_name`, `contact_person`, or `full_billing_address` (e.g. `<img src=x onerror="alert(document.cookie)">`).
  3. Profile updates are persisted to `apps.customers.models.Customer`.
  4. When the customer or an internal finance staff member views or downloads the invoice HTML via `/api/v1/portal/invoices/{id}/download/`, the server constructs an HTML document using an unescaped Python `f-string`.
  5. The attacker's JavaScript executes in the context of the user viewing the invoice.
- **Failure Scenario:** Session hijacking, unauthorized API actions triggered from staff browser sessions, data exfiltration.
- **Remediation:** Refactor `PortalInvoiceDownloadView` to use auto-escaping template rendering or explicit `html.escape()` on all dynamic customer/invoice fields before outputting to the HTTP response.

---

### SEC-02: Permissive CORS Configuration and Open Host Header
- **Affected File:** `backend/brightloop/settings.py`
- **Severity:** Medium
- **Attack Vector:**
  - `CORS_ALLOW_ALL_ORIGINS = True` was paired with `CORS_ALLOW_CREDENTIALS = True`. This creates security vulnerabilities and violates modern browser cross-origin credential policies.
  - `ALLOWED_HOSTS = ['*']` allows arbitrary `Host` headers, exposing the application to DNS rebinding, cache poisoning, and password reset poisoning attacks.
- **Remediation:**
  - Explicitly define `CORS_ALLOWED_ORIGINS` to include only trusted origins (`http://localhost:5173`, `http://127.0.0.1:5173`, etc.).
  - Set `CORS_ALLOW_ALL_ORIGINS = False`.
  - Read `ALLOWED_HOSTS` from an environment variable, defaulting strictly to `localhost,127.0.0.1`.

---

### SEC-03: Hardcoded Secret Key Fallback
- **Affected File:** `backend/brightloop/settings.py`
- **Severity:** Medium
- **Attack Vector:** A hardcoded static secret key was committed in settings without fallback warning or environment extraction. If deployed in production without setting `SECRET_KEY`, signed session cookies and cryptographic tokens can be forged.
- **Remediation:** Read `SECRET_KEY` from `os.environ.get('SECRET_KEY')` and emit an explicit warning or require it in production mode (`DEBUG = False`).

---

### GAP-01: Missing Append-Only Audit Logging on Financial & Identity Actions
- **Affected Files:** `backend/apps/payments/services.py`, `backend/apps/billing/views.py`, `backend/brightloop/settings.py`
- **Severity:** High
- **PRD Invariant:** PRD §4.1, PRD §7.1, and contract require all identity events, payments, reversals, and invoice state transitions to be recorded in an immutable, append-only audit trail.
- **Defect:** `backend(teammate 1)` designed an append-only audit log model with database-level trigger immutability (`0002_append_only_trigger.py`), but the audit application was not integrated into `backend/apps/audit/` or called during payment creation, payment reversal, or invoice cancellation.
- **Remediation:**
  1. Integrate `apps.audit` into `backend/apps/audit/`.
  2. Install the database trigger ensuring UPDATE and DELETE operations on `brightloop_audit_logs` raise exceptions at the database engine level.
  3. Instrument `record_payment` and `reverse_payment` in `apps.payments.services` with `record_audit`.
  4. Instrument `invoice_cancel` and `invoice_send` in `apps.billing.views` with `record_audit`.

---

### GAP-02: Missing API Mounts for Audit, Staff, and Billing V1 Routes
- **Affected File:** `backend/brightloop/urls.py`
- **Severity:** Medium
- **Defect:** Routes for `/api/v1/audit/` and `/api/v1/staff/` were not exposed in root URLs. Furthermore, billing routes were only mounted at `/billing/`, causing `/api/v1/billing/...` calls from unified frontend clients to return 404.
- **Remediation:** Expose `/api/v1/audit/`, `/api/v1/staff/`, and alias `/api/v1/billing/` to `apps.billing.urls`.

---

### HARD-01: Demo Shortcuts and Hardcoded Plaintext Credentials in Frontend
- **Affected File:** `frontend/src/components/LoginModal.tsx`
- **Severity:** Medium
- **Defect:** The login modal included a "Quick Demo Accounts" panel with hardcoded emails and passwords (`FinanceSecure@123`, `AdminSecure@123`, etc.).
- **Remediation:** Remove the entire demo credentials section. All logins must pass through authentic credential submission against `/api/v1/auth/login/`.

---

### HARD-02: Redundant Duplicate Configuration Block in Django Settings
- **Affected File:** `backend/brightloop/settings.py`
- **Severity:** Low
- **Defect:** Lines 129-133 contained an exact duplicate of lines 123-127 (`BILLING_PAYMENT_MODEL`, `DEFAULT_FROM_EMAIL`, etc.).
- **Remediation:** Remove the duplicated block to maintain configuration cleanliness and clarity.

---

## 3. Verification & Remediation Plan

1. **Security Hardening:** Update `PortalInvoiceDownloadView` with HTML-safe escaping to eliminate XSS.
2. **Environment & CORS Tightening:** Refactor `settings.py` to use environment variables for `SECRET_KEY`, `ALLOWED_HOSTS`, and explicit `CORS_ALLOWED_ORIGINS`.
3. **Audit Trail Integration:** Integrate `apps.audit` into `backend/apps/audit/`, run migrations, and instrument financial service hooks.
4. **Clean Frontend:** Strip all hardcoded passwords and demo shortcuts from `LoginModal.tsx`.
5. **End-to-End Verification:** Execute all unit/integration tests and verify clean TypeScript build.

