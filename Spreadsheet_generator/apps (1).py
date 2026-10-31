from django.apps import AppConfig


class RegisterConfig(AppConfig):
    name = "register"

    def ready(self):
        from . import signals  # noqa: F401
