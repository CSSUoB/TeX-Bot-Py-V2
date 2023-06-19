"""
    Configurations to make core app ready to import into settings.py.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
        Class acting as a container of all the configuration required for the
        core app. Extends the AppConfig class which contains the methods to
        initialise the app, apply migrations etc.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "db.core"
