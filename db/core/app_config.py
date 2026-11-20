"""Configurations to make the core app ready to import into _settings.py."""

__all__: Sequence[str] = ("CoreConfig",)

lazy from collections.abc import Sequence

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Contains all the configuration required for the core app.

    Extends the django.apps.AppConfig class which contains the methods to initialise the app,
    apply migrations, etc.
    """

    name: str = "db.core"
