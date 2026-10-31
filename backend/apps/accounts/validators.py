import re

from django.core.exceptions import ValidationError

MIN_LENGTH = 9


class BrightloopPasswordValidator:
    """PRD 7.1: at least 9 characters, upper case, lower case and a special character."""

    def validate(self, password: str, user=None) -> None:
        errors = []
        if len(password) < MIN_LENGTH:
            errors.append(
                ValidationError(
                    "Password must be at least %(min)d characters long.",
                    code="password_too_short",
                    params={"min": MIN_LENGTH},
                )
            )
        if not re.search(r"[A-Z]", password):
            errors.append(
                ValidationError(
                    "Password must contain at least one uppercase letter.",
                    code="password_no_upper",
                )
            )
        if not re.search(r"[a-z]", password):
            errors.append(
                ValidationError(
                    "Password must contain at least one lowercase letter.",
                    code="password_no_lower",
                )
            )
        if not re.search(r"[^A-Za-z0-9\s]", password):
            errors.append(
                ValidationError(
                    "Password must contain at least one special character.",
                    code="password_no_special",
                )
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self) -> str:
        return (
            f"Your password must be at least {MIN_LENGTH} characters and contain an "
            "uppercase letter, a lowercase letter and a special character."
        )
