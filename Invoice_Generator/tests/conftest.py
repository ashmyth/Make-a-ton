import os
import sys
from decimal import Decimal
import django
from django.conf import settings

# Ensure Invoice_Generator is in sys.path as 'billing' or mapped
INVOICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(INVOICE_DIR)

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Alias Invoice_Generator package as billing so 'import billing' resolves seamlessly
import Invoice_Generator
sys.modules["billing"] = Invoice_Generator

# Configure minimal Django settings for testing
if not settings.configured:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key-make-a-ton-billing",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "billing.apps.BillingConfig",
            "billing.tests.mock_payments",
        ],
        ROOT_URLCONF="billing.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [os.path.join(BASE_DIR, "templates")],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Brightloop <billing@brightloop.com>",
        BILLING_PAYMENT_MODEL="mock_payments.Payment",
        BILLING_COMPANY_NAME="Brightloop",
        SUPABASE_URL="",
        SUPABASE_SERVICE_ROLE_KEY="",
        SUPABASE_INVOICE_BUCKET="invoices",
    )
    django.setup()
