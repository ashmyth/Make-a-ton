# Brightloop Tech Stack

**Version:** 2.0
**Status:** Proposed
**Applies to:** Brightloop Subscription Management Platform PRD v1.0

Every technology below exists because a specific PRD requirement forces it. Every rejected alternative has a stated reason.

---

## 1. Architecture at a Glance

```
Browser (React SPA, static files)
        │  same origin
Caddy reverse proxy ── /      → static SPA build
        │             └ /api  → Django (gunicorn)
        ▼
Django + DRF (modular monolith)
        │                         │
        ▼                         ▼
PostgreSQL (all state)      Object storage (invoice PDFs)
   ▲
   │ jobs, locks, billing state, audit
Procrastinate worker (PDF, email, billing sweep)
```

Production runs **three processes** (Caddy, web, worker) and **two stateful systems** (PostgreSQL, object storage).

---

## 2. Final Stack

| Layer | Choice | PRD Driver |
| --- | --- | --- |
| Frontend framework | Vite + React + strict TypeScript | Console and portal surfaces; no SSR needed for an authenticated app |
| Routing | TanStack Router (typed routes and search params) | Typed filters (§7.13); separate lazy-loaded `/console` and `/portal` trees |
| UI | Tailwind CSS + shadcn/ui (Radix) | Accessible dashboards and forms |
| Data and forms | TanStack Query, TanStack Table (virtualized), react-hook-form + zod | Thousands of records, filters, validated forms |
| API client | drf-spectacular → Orval (generated, typed) | Frontend and backend contract cannot drift |
| Money math | Backend preview endpoint only | §8: same calculation service for previews and invoices |
| Reverse proxy | Caddy | Same-origin serving, automatic TLS, no CORS |
| Backend | Django 5 + Django REST Framework, modular monolith | Financial logic, RBAC, atomic writes |
| Domain apps | `identity`, `catalog`, `subscriptions`, `billing`, `payments`, `reporting`, `audit` (boundaries enforced by import-linter: `identity`/`catalog` → `subscriptions` → `billing` → `payments` → `reporting`) | Clear ownership, testable services, acyclic dependency graph |
| Database | PostgreSQL | See section 3 |
| Background jobs | Procrastinate (Postgres-backed, Django integration) | BILL-01 to BILL-05 |
| Sessions and cache | Django database sessions and DB cache backend | AUTH-06, DRF throttling; no Redis |
| Email uniqueness | `citext` column with unique index | AUTH-01: one account per email |
| Auth | Django sessions, argon2, custom password validator, django-axes | §7.1, AUTH-01 to AUTH-06 |
| Email delivery | SES or Postmark via django-anymail, plus `EmailLog` table | Password reset and invoice sending |
| PDF | WeasyPrint, rendered in the worker, stored at confirmation | §7.9 printable, reproducible invoices |
| File storage | S3-compatible object storage; signed URLs after ownership check | Customers download own invoices only |
| Audit | django-pghistory (trigger-based) | Audit history, payment reversals |
| API docs | drf-spectacular (OpenAPI) | Documented, typed contract |

---

## 3. How PostgreSQL Satisfies Financial & Billing Rules

### 3.1 Recurring Billing Rules (Teammate 3)

| Requirement | Mechanism |
| --- | --- |
| No duplicate invoice per period (BILL-01) | Unique constraint on `(subscription_id, period_start, period_end)` |
| Invoice and checkpoint are atomic (BILL-02) | One transaction creates the invoice and advances `next_billing_date` |
| No lost or duplicate side effects | PDF and email jobs are enqueued in the same transaction as the invoice; a rollback means the job never existed |
| Safe retries (BILL-03) | Idempotent period key plus Procrastinate retry policy |
| One failure does not block the batch (BILL-04) | Daily sweep queries due subscriptions and defers one job per subscription |
| No double scheduling | Periodic tasks are deduplicated in the database, so multiple workers are safe |
| Per-subscription serialization | Procrastinate job locks keyed by subscription ID |
| Visible failures (BILL-05) | `billing_failure` table plus job status rows feed the operations queue and retry endpoint |
| Missed periods after downtime (BILL-06) | Sweep recomputes due periods from the database; one invoice per period |
| Discount usage limits under parallel jobs | Reservation rows guarded by row locks (never in-memory counters) |
| Immutable confirmed invoices | Snapshot columns, FSM-guarded status, DB trigger blocking financial updates |

### 3.2 Payment & Allocation Rules (Teammate 4)

| Requirement | Mechanism |
| --- | --- |
| Invoice-first allocation (PAY-01) | Invoices are created first by billing sweeps; payments are allocated to existing confirmed invoices (`Payment.invoice_id` with `on_delete=PROTECT`). Payments never generate invoices. |
| Idempotent payment recording (PAY-02) | Unique constraint on `Payment.idempotency_key` prevents double-recording from duplicate clicks, retries, or replays. |
| Overpayment prevention (PAY-03) | `CHECK (outstanding_balance >= 0)` on `Invoice` + `select_for_update()` row-level lock on `Invoice` during payment recording. |
| Audited reversals (PAY-04) | Payments cannot be deleted; corrections use append-only reversal records (`is_reversed`, `reversed_at`, `reversed_by`, `reversal_reason`) tracked via `django-pghistory`. |
| Atomic balance & status sync (PAY-05) | Payment creation or reversal executes in a single transaction that updates the payment ledger and atomically recalculates `Invoice.outstanding_balance` and `Invoice.status`. |
| Gateway-ready data schema (PAY-06) | `Payment` stores `method`, `amount`, `currency`, and `external_reference` (indexed for future gateway webhook IDs, bank UTR, or cheque numbers) allowing V2 gateway adapters without core schema changes. |
| Customer data isolation | Scoped querysets, DRF permission classes, Postgres row-level security ensuring portal users only access their own invoices/payments. |
| Dashboard reconciles with records | Live indexed SQL aggregates (`SUM(Payment.amount)` for cash collected, `SUM(Invoice.outstanding_balance)` for receivables); no cached totals. |
| Exact money | `numeric` columns with CHECK constraints (non-negative amounts, `start <= expiry`). |

---

## 4. Calculation and Date Policy

- Python `Decimal` throughout; one global rounding mode (`ROUND_HALF_UP`) in a single `calculation` module.
- Tax rounded per line; invoice total is the sum of rounded lines (PRD §8).
- Frontend never computes money; it calls the backend preview endpoint.
- `USE_TZ=True`, one configured business timezone via `zoneinfo`; billing anchors stored as `DateField`.
- Billing dates computed as `anchor + n months` from the original anchor using `dateutil.relativedelta`, never from the previous date (month-end clamping, anchor preserved).

---

## 5. Decision Register (Former Open Items)

Each item gets an ADR stating the decision, the reason, the approving owner, and what changes if it flips.

| Open Item | Pinned Default | Swappable Via |
| --- | --- | --- |
| Proration | None; full periods only (PRD BILL-08) | `ProrationPolicy` interface |
| Final partial period | Never bill past expiry; flag "Expired, action required" | Period calculator module |
| Refunds and credit notes | Out of scope; payment reversals only | New ledger entry type |
| Plan vs product pricing | PRD §7.4 rule as written | `pricing` service and golden tests |
| Pause/resume adjustments | Pause stops future invoices; no credits issued | Policy interface |
| Invoice & Payment sequence | Invoices are generated first (by billing sweeps or quotation conversion); payments are allocated to existing confirmed invoices. Payments never generate draft invoices. | Workstream workflow contract |
| Payment gateway scope | V1 uses staff recording and manual bank transfers with an idempotent, gateway-ready data model. Live gateways and webhooks are pluggable adapters deferred to V2 per PRD §5.2. | `PaymentGatewayAdapter` interface |

---

## 6. Quality and Testing

| Concern | Tool |
| --- | --- |
| Backend | pytest, pytest-django, factory_boy |
| Calculation correctness | Hypothesis property tests; golden tests from PRD examples (4,950 invoice; 400/600 payments) |
| Concurrency and idempotency | `transactional_db` tests running billing in parallel, asserting one invoice per period |
| Date logic | time-machine (month-end clamping, downtime recovery) |
| Static checks | mypy strict with django-stubs, ruff, eslint, import-linter |
| Frontend | Vitest, Testing Library, Playwright, axe |
| Access control | Explicit IDOR tests; test asserting cost price absent from customer serializers |
| Load | k6 against 50k seeded subscriptions; p95 under 2 seconds |
| Query health | Query-count assertions to catch N+1 regressions |

---

## 7. Platform and Operations

| Concern | Choice |
| --- | --- |
| Containers | Docker: Caddy, web (gunicorn), worker |
| Database | Managed PostgreSQL with backups |
| CI/CD | GitHub Actions: tests, django-migration-linter, Trivy scan, SBOM |
| Infrastructure | Terraform; docker-compose for local setup |
| Observability | OpenTelemetry, Sentry, structlog, Grafana (billing runs, failures, queue depth from Postgres) |
| Security | CSP headers, secret manager, Dependabot, documented threat model |
| Documentation | ADRs, C4 diagram, OpenAPI |

---

## 8. Tradeoffs to Record as ADRs

- **Procrastinate** has a smaller community than Celery and lower peak throughput than Redis queues, though far above what thousands of subscriptions need. Keep a thin `jobs` interface so it can be swapped.
- **Connection pooling:** Procrastinate workers use LISTEN/NOTIFY, which does not work through PgBouncer in transaction mode. Connect workers directly or use session pooling; keep the pooler for the web process.
- **No SSR:** fine for an authenticated app, but rules out public marketing pages in this codebase.
- **DB-backed sessions and cache** add small read load to Postgres. Negligible at this scale; include expired-row cleanup in maintenance jobs.
- **Django Admin** is disabled or read-only for financial models, since it bypasses the service layer, validation, and immutability rules.

---

## 9. Rejected Alternatives

| Alternative | Reason Rejected |
| --- | --- |
| Microservices | Money writes need single-transaction consistency |
| Kafka / event sourcing | Scale is thousands of subscriptions; same-transaction job enqueue is sufficient |
| Redis as billing state | Not durable by default; risks the zero-duplicate guarantee |
| Celery + Redis | Extra stateful system and Beat single-instance hazard; Procrastinate gives transactional enqueue |
| Next.js | No SSR need; adds a runtime, CORS/CSRF complexity, and a middleware-auth surface |
| JWT in localStorage | XSS-exposed; HttpOnly session cookies are safer for a financial app |
| Django Admin for financial models | Bypasses services and immutability rules |
| Frontend money calculation | JS floats drift from backend decimals |
| GraphQL | REST with OpenAPI gives simpler permissions and typed clients here |
| Kubernetes | Operational cost outweighs benefit at this scale |
| Payment gateway (live webhooks) in V1 | Excluded by PRD §5.2 to avoid webhook/tunnel fragility during MVP; append-only schema is gateway-ready for V2 |

---

## 10. Suggested Build Order

1. Domain models, constraints, and the calculation service, with property tests.
2. Billing engine: recurring billing sweep, invoice generation, idempotency, same-transaction job enqueue.
3. Payments ledger & allocation service: idempotent payment recording against confirmed invoices, atomic balance updates, reversals, and customer portal views.
4. API layer with permissions and generated client.
5. Frontend console and customer portal.
6. Observability, load tests, and CI hardening.
