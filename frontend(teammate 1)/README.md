# Brightloop Frontend — Teammate 1: Identity & Customer Foundation

Interactive React + TypeScript + Tailwind CSS user interface for **Teammate 1** (Identity, Access & Customer Foundation), adhering to [`TECK_STACK.md`](file:///d:/Make-a-ton/TECK_STACK.md) and PRD v1.0.

---

## 1. Features & Screens Implemented

### A. Authentication & Security (PRD §7.1)
- **Sign In Modal:** Session-based authentication with lockout notices (HTTP 429 after 5 failed attempts).
- **Customer Registration:** Validates PRD password criteria in real-time (9+ characters, uppercase, lowercase, special character).
- **Password Recovery:** Single-use, expiring token request with neutral responses (`AUTH-04`) to prevent user enumeration.

### B. Admin Staff Management Console (PRD §4.1 & `work division.md`)
- **Staff List:** Displays all staff members, email, role badge (`OPERATIONS`, `FINANCE`, `ADMINISTRATOR`), and active status.
- **Add Staff Modal:** Administrator workflow to create staff accounts with role assignment and password validation.
- **Soft Deactivation (`AUTH-05`):** Deactivates staff access (`is_active = False`) while preserving all historical documents, quotations, and audit records.
- **Safeguards:** Self-deactivation prevention for the acting administrator.

### C. Customer Management CRM (PRD §7.2)
- **Customer Table:** Live search by name, email, customer code (`CUST-...`), and contact person.
- **Status & Type Filters:** Filter by Active/Archived status and Business/Individual account type.
- **Create Customer Modal:** Full form supporting Business and Individual entities, billing addresses, tax identifiers (VAT/GST/EIN), and default payment terms (`IMMEDIATE`, `NET_15`, `NET_30`, `NET_60`).
- **Customer Detail Drawer:** View complete profile and billing address snapshots.
- **Soft Archive / Restore:** Soft-archive customer records without deleting historical quotations or invoices.
- **Portal Account Linking:** Link existing user accounts or create new customer portal credentials.

### D. Customer Self-Service Portal (PRD §4.2)
- Scoped to `request.user.customer_id`.
- Customers can view their account overview and update permitted contact information and billing addresses.
- Rejects attempts to edit commercial terms (`status`, `payment_terms`, `tax_identifier`).

### E. Immutable Security Audit Trail (PRD §7 & `TECK_STACK.md` §3)
- Real-time audit log viewer showing timestamp, event action, actor, target entity, client IP, and JSON payload diffs.

---

## 2. Component Structure

```
frontend/
├── src/
│   ├── types/
│   │   └── index.ts                 # TypeScript types (UserProfile, Customer, StaffMember, AuditLogEntry)
│   ├── services/
│   │   └── api.ts                   # Typed API service with CSRF handling & session credentials
│   ├── components/
│   │   ├── auth/
│   │   │   └── AuthModal.tsx        # Login, Register, Forgot Password, Reset Password
│   │   ├── staff/
│   │   │   └── StaffManagement.tsx  # Staff table, Add Staff, Soft Deactivate
│   │   ├── customers/
│   │   │   └── CustomerManagement.tsx # CRM table, search, filters, create customer, detail drawer
│   │   ├── portal/
│   │   │   └── CustomerPortalView.tsx # Customer self-service profile & address editor
│   │   └── audit/
│   │       └── AuditTrail.tsx       # Immutable audit log viewer
│   ├── App.tsx                      # Top nav, role-based tabs, user profile badge, logout
│   ├── main.tsx                     # React root mount
│   └── index.css                    # Tailwind CSS directives
├── standalone_preview.html          # Zero-dependency interactive web console
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

---

## 3. How to Launch & Test

### Option A: Open the Interactive Standalone Console (Instant, zero-install)
Open `standalone_preview.html` directly in any modern browser:
```bash
# In your browser, open:
file:///d:/Make-a-ton/frontend/standalone_preview.html
```
This provides a complete interactive experience with simulated live roles (`ADMINISTRATOR`, `OPERATIONS`, `FINANCE`, `CUSTOMER`), real-time PRD password validation meter, 5-attempt rate-limit lockout simulation, customer CRM creation, soft-deactivation, and audit inspection.

### Option B: Run Vite Development Server
```bash
npm install
npm run dev
```
The app will be served at `http://localhost:5173` with automatic API proxying to `http://localhost:8000/api/v1/`.

