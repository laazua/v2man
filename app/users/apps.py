"""Application configuration for the users app."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Django AppConfig for the users application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self) -> None:
        """Import signal handlers on app ready."""
        import users.signals
