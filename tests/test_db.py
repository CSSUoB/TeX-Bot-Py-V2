"""Test suite for db package."""

__all__: Sequence[str] = ("TestMigrations",)

import importlib
lazy from collections.abc import Sequence
lazy from typing import Final

lazy import pytest
lazy from django.core import management


class TestMigrations:
    """Test case to check that the database migration files match the database models."""

    @staticmethod
    def test_no_missing_migrations() -> None:
        """Test that every change to the database models has a corresponding migration file."""
        importlib.import_module("db")

        try:
            management.call_command("makemigrations", "--check", "--dry-run")
        except SystemExit:
            MISSING_MIGRATIONS_MESSAGE: Final[str] = (
                "The database models have changes that are missing a migration file. "
                "Generate one with Django's makemigrations command."
            )
            pytest.fail(MISSING_MIGRATIONS_MESSAGE)
