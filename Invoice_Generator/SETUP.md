# Billing app setup (Django + Supabase Postgres + Supabase Storage)

## 1. Install
```
pip install django "psycopg[binary]" dj-database-url python-dotenv supabase xhtml2pdf pytest
```

## 2. settings.py additions
```python
import os, dj_database_url
from dotenv import load_dotenv
load_dotenv()

INSTALLED_APPS += ["billing"]

# Supabase Postgres (Dashboard -> Connect -> Session pooler URI)
DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=0, ssl_require=True)
}
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True  # needed for transaction pooler

# Teammate 4's payment model, "app_label.ModelName"
BILLING_PAYMENT_MODEL = "payments.Payment"
BILLING_COMPANY_NAME = "Brightloop"

# Supabase Storage
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
SUPABASE_INVOICE_BUCKET = "invoices"

# Email (Supabase does not send app mail. Use SMTP: Gmail app password, Resend, Brevo...)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
DEFAULT_FROM_EMAIL = "Brightloop <billing@yourdomain.com>"
```
Dev tip: `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` prints mail in terminal.

## 3. .env
```
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role key>
EMAIL_HOST=...
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```
Add `.env` to `.gitignore`.

## 4. Migrate
```
python manage.py makemigrations billing
python manage.py migrate
```

## 5. Edit adapters
Open `billing/services/adapters.py`, match field names to Teammate 2 (subscription lines)
and Teammate 4 (payment). Only that file touches their models.

## 6. Staff dashboard URLs + permissions
Project `urls.py`:
```python
path("", include("billing.urls")),
```
Needs `django.contrib.messages` + `django.contrib.auth` (default in Django).
Dashboard: `/staff/invoices/`

Permissions (Django admin -> Groups):
- `billing | invoice | Can view invoice`  -> see list, detail, PDF preview
- `billing | invoice | Can send invoices to customers` -> Send / Resend button
Superuser has all. Customers must have neither.

## 7. Schedule retry (missing invoices only)
```
*/5 * * * *  cd /app && python manage.py retry_failed_invoices
```
Emails are never auto-sent or auto-retried. Staff clicks Send.

## 8. Test
```
pytest billing/tests
```
