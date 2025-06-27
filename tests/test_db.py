"""
Complete database testing suite with isolated test database setup.

This file contains EVERYTHING needed for Django database testing:
- Django configuration and setup (replaces conftest.py)
- Database isolation using pytest-django
- Comprehensive tests for all database models
- No interference with production database
- Run with: uv run pytest tests/test_db.py

The pytest-django plugin handles database creation, isolation, and cleanup.
Each test gets a fresh, empty test database that never touches production data.
"""

import os
import re
from pathlib import Path

import django
import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db._settings")
if not settings.configured:
    django.setup()

from db.core.models import DiscordMember, DiscordReminder


@pytest.mark.django_db()
class TestDiscordReminder:
    """Test suite for the DiscordReminder class with database isolation."""

    def test_successful_reminder_creation(self) -> None:
        """Test that a DiscordReminder can be created successfully."""
        # First create a DiscordMember (required foreign key)
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        reminder = DiscordReminder.objects.create(
            discord_member=discord_member,
            message="This is a test reminder.",
            _channel_id="987654321098765432",
            send_datetime="2025-06-25T12:00:00Z",
            _channel_type=1,
        )

        assert DiscordReminder.objects.all().count() == 1
        retrieved_reminder = DiscordReminder.objects.get(
            discord_member=discord_member,
        )
        assert retrieved_reminder == reminder
        assert retrieved_reminder.message == "This is a test reminder."
        assert retrieved_reminder.channel_id == 987654321098765432
        assert retrieved_reminder._channel_type == 1  # noqa: SLF001

    def test_reminder_channel_id_property(self) -> None:
        """Test the channel_id property getter and setter."""
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        reminder = DiscordReminder.objects.create(
            discord_member=discord_member,
            message="Test message",
            _channel_id="123456789012345678",
            send_datetime="2025-06-25T12:00:00Z",
            _channel_type=0,
        )

        assert reminder.channel_id == 123456789012345678
        assert isinstance(reminder.channel_id, int)

        reminder.channel_id = "987654321098765432"
        assert reminder._channel_id == "987654321098765432"  # noqa: SLF001
        assert reminder.channel_id == 987654321098765432

    def test_reminder_invalid_channel_id(self) -> None:
        """Test that invalid channel IDs raise validation errors."""
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        reminder = DiscordReminder(
            discord_member=discord_member,
            message="Test message",
            _channel_id="123",
            send_datetime="2025-06-25T12:00:00Z",
            _channel_type=0,
        )
        with pytest.raises(ValidationError):
            reminder.full_clean()

    def test_reminder_cascade_delete(self) -> None:
        """Test that reminders are deleted when the associated DiscordMember is deleted."""
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        DiscordReminder.objects.create(
            discord_member=discord_member,
            message="Test message",
            _channel_id="987654321098765432",
            send_datetime="2025-06-25T12:00:00Z",
            _channel_type=1,
        )

        assert DiscordReminder.objects.count() == 1

        discord_member.delete()

        assert DiscordReminder.objects.count() == 0

    def test_multiple_reminders_same_user(self) -> None:
        """Test that a user can have multiple reminders."""
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        reminder1 = DiscordReminder.objects.create(
            discord_member=discord_member,
            message="First reminder",
            _channel_id="987654321098765432",
            send_datetime="2025-06-25T12:00:00Z",
            _channel_type=1,
        )

        reminder2 = DiscordReminder.objects.create(
            discord_member=discord_member,
            message="Second reminder",
            _channel_id="987654321098765432",
            send_datetime="2025-06-26T12:00:00Z",
            _channel_type=1,
        )

        assert DiscordReminder.objects.count() == 2
        assert discord_member.reminders.count() == 2

        reminders = list(discord_member.reminders.all())
        assert reminder1 in reminders
        assert reminder2 in reminders

    def test_database_isolation_example(self) -> None:
        """
        Demonstrate database isolation between tests.

        This test shows that:
        1. Each test gets a fresh, empty database
        2. Changes made in one test don't affect other tests
        3. The production database is never touched
        """
        db_name = settings.DATABASES["default"]["NAME"]
        db_path = Path(str(db_name))
        assert (
            "test_" in str(db_path) or ":memory:" in str(db_name) or "memorydb" in str(db_name)
        )

        assert DiscordMember.objects.count() == 0
        assert DiscordReminder.objects.count() == 0

        member = DiscordMember.objects.create(discord_id="123456789012345678")
        reminder = DiscordReminder.objects.create(
            discord_member=member,
            message="Test reminder for isolation",
            _channel_id="987654321098765432",
            send_datetime="2025-06-25T12:00:00Z",
            _channel_type=0,
        )

        assert DiscordMember.objects.count() == 1
        assert DiscordReminder.objects.count() == 1
        assert reminder.message == "Test reminder for isolation"

    def test_fresh_database_for_each_test(self) -> None:
        """
        Verify that each test gets a fresh database.

        Even though other tests created data, this test starts
        with an empty database because pytest-django provides
        database isolation.
        """
        assert DiscordMember.objects.count() == 0
        assert DiscordReminder.objects.count() == 0

        member = DiscordMember.objects.create(discord_id="999888777666555444")

        assert DiscordMember.objects.count() == 1
        assert member.discord_id == "999888777666555444"

    def test_unique_constraint_violation(self) -> None:
        """Test that unique constraints are properly enforced."""
        DiscordMember.objects.create(discord_id="123456789012345678")

        with pytest.raises(
            ValidationError,
            match=re.escape(
                "'discord_id': ['Discord member with this Discord Member ID already exists.']"
            ),
        ):
            DiscordMember.objects.create(discord_id="123456789012345678")

    def test_foreign_key_relationship(self) -> None:
        """Test the foreign key relationship between DiscordMember and DiscordReminder."""
        member = DiscordMember.objects.create(discord_id="123456789012345678")

        for i in range(3):
            DiscordReminder.objects.create(
                discord_member=member,
                message=f"Reminder {i}",
                _channel_id="987654321098765432",
                send_datetime=f"2025-06-{25 + i}T12:00:00Z",
                _channel_type=0,
            )

        assert member.reminders.count() == 3
        assert all(reminder.discord_member == member for reminder in member.reminders.all())

        # Test reverse relationship
        first_reminder = member.reminders.first()
        assert first_reminder is not None
        assert first_reminder.discord_member.discord_id == "123456789012345678"


@pytest.mark.django_db()
def test_standalone_database_function() -> None:
    """Example of a standalone test function (not in a class)."""
    member = DiscordMember.objects.create(discord_id="111222333444555666")

    assert DiscordMember.objects.filter(discord_id="111222333444555666").exists()
    assert str(member) == "111222333444555666"


@pytest.mark.django_db(transaction=True)
def test_with_transaction_support() -> None:
    """Example test that requires transaction support."""
    member = DiscordMember.objects.create(discord_id="777888999000111222")

    class TestRollbackError(Exception):
        """Custom exception for testing transaction rollback."""

    def _force_rollback() -> None:
        """Force a transaction rollback for testing purposes."""
        msg = "Rollback test"
        raise TestRollbackError(msg)

    try:
        with transaction.atomic():
            DiscordReminder.objects.create(
                discord_member=member,
                message="This will be rolled back",
                _channel_id="987654321098765432",
                send_datetime="2025-06-25T12:00:00Z",
                _channel_type=0,
            )
            _force_rollback()
    except TestRollbackError:
        pass

    assert DiscordMember.objects.filter(discord_id="777888999000111222").exists()
    assert not DiscordReminder.objects.filter(discord_member=member).exists()
