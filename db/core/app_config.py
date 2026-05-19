"""Configurations to make the core app ready to import into _settings.py."""

from typing import TYPE_CHECKING

from django.apps import AppConfig

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: Sequence[str] = ("CoreConfig",)


class CoreConfig(AppConfig):
    """
    Contains all the configuration required for the core app.

    Extends the django.apps.AppConfig class which contains the methods to initialise the app,
    apply migrations, etc.
    """

    name: str = "db.core"
