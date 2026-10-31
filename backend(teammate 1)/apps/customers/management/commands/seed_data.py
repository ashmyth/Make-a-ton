import os
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.access_control.roles import UserRole
from apps.customers.models import Customer

SEED_USERS = [
    ("ADMIN", "admin@brightloop.io", UserRole.ADMINISTRATOR, "System", "Admin"),
    ("OPS", "ops@brightloop.io", UserRole.OPERATIONS, "Operations", "Console"),
    ("FINANCE", "finance@brightloop.io", UserRole.FINANCE, "Finance", "Console"),
    ("CUSTOMER", "alice@acmecorp.com", UserRole.CUSTOMER, "Alice", "Anderson"),
]


def random_password() -> str:
    """Random password that satisfies the Brightloop password policy."""
    alphabet = string.ascii_letters + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(14))
    return (
        f"{secrets.choice(string.ascii_uppercase)}{secrets.choice(string.ascii_lowercase)}!{body}"
    )


class Command(BaseCommand):
    help = (
        "Create one demo account per role plus a linked demo customer. Development only. "
        "Set SEED_<ROLE>_PASSWORD (ADMIN, OPS, FINANCE, CUSTOMER) or a random password is "
        "generated and printed once. Existing accounts are left untouched."
    )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_data only runs with DEBUG=true.")
        User = get_user_model()
        created_users = {}
        with transaction.atomic():
            for key, email, role, first, last in SEED_USERS:
                user = User.objects.filter(email=email).first()
                if user is not None:
                    self.stdout.write(f"exists  {email}")
                    created_users[key] = user
                    continue
                password = os.environ.get(f"SEED_{key}_PASSWORD") or random_password()
                user = User.objects.create_user(
                    email=email, password=password, role=role, first_name=first, last_name=last
                )
                created_users[key] = user
                shown = "(from environment)" if os.environ.get(f"SEED_{key}_PASSWORD") else password
                self.stdout.write(f"created {email} [{role}] password: {shown}")

            alice = created_users["CUSTOMER"]
            if alice.customer is None:
                Customer.objects.create_with_code(
                    customer_type=Customer.CustomerType.BUSINESS,
                    display_name="Acme Corporation",
                    contact_person="Alice Anderson",
                    email=alice.email,
                    phone="+1 555 0100",
                    billing_street="1 Market Street",
                    billing_city="San Francisco",
                    billing_state="CA",
                    billing_postal_code="94105",
                    billing_country="US",
                    payment_terms=Customer.PaymentTerms.NET_30,
                    portal_user=alice,
                )
                self.stdout.write("created customer Acme Corporation linked to alice@acmecorp.com")
