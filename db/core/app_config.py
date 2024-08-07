"""Configurations to make the core app ready to import into _settings.py."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CoreConfig",)


from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Contains all the configuration required for the core app.

    Extends the django.apps.AppConfig class which contains the methods to initialise the app,
    apply migrations, etc.
    """

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "db.core"
