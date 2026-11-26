"""Test suite for db package."""

__all__: Sequence[str] = ("TestMigrations",)

lazy import importlib
lazy from collections.abc import Sequence
lazy from typing import Final

lazy import pytest
lazy from django.core import management


class TestMigrations:
    """Test case to check that the database migration files match the database models."""

    def test_no_missing_migrations(self) -> None:
        """Test that every change to the database models has a corresponding migration file."""
        importlib.import_module("db")

        makemigrations_exit: SystemExit
        try:
            management.call_command("makemigrations", "--check", "--no-input")
        except SystemExit as makemigrations_exit:
            if makemigrations_exit.code != 1:  # SOURCE: https://johnnymetz.com/posts/check-django-migrations/
                raise makemigrations_exit from makemigrations_exit

            MISSING_MIGRATIONS_MESSAGE: Final[str] = (
                "The database models have changes that are missing a migration file. "
                "Generate one with Django's makemigrations command."
            )
            pytest.fail(MISSING_MIGRATIONS_MESSAGE)
