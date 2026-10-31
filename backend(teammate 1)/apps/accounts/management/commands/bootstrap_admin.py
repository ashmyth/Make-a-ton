import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.access_control.roles import UserRole
from apps.accounts.models import normalize_email


class Command(BaseCommand):
    help = (
        "Create the first Administrator account. Password comes from "
        "BOOTSTRAP_ADMIN_PASSWORD or an interactive prompt."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--first-name", default="")
        parser.add_argument("--last-name", default="")

    def handle(self, *args, **options):
        User = get_user_model()
        email = normalize_email(options["email"])
        if User.objects.filter(email=email).exists():
            raise CommandError(f"A user with email {email} already exists.")
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD") or getpass.getpass("Password: ")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        user = User.objects.create_user(
            email=email,
            password=password,
            role=UserRole.ADMINISTRATOR,
            first_name=options["first_name"],
            last_name=options["last_name"],
        )
        self.stdout.write(self.style.SUCCESS(f"Administrator {user.email} created."))
