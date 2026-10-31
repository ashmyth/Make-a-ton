from django.db import models


class CIEmailField(models.EmailField):
    """Email column stored as PostgreSQL ``citext`` (case-insensitive uniqueness).

    Django 5.1 removed ``django.contrib.postgres.fields.CIEmailField``; this is the
    minimal replacement. Requires the ``citext`` extension (created in migration 0001).
    Falls back gracefully to standard varchar for SQLite test runs.
    """

    def db_type(self, connection) -> str:
        if connection.vendor == "postgresql":
            return "citext"
        return "varchar(254)"

    def get_internal_type(self) -> str:
        return "EmailField"
