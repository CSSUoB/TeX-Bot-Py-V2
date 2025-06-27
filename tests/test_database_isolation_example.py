"""
Example demonstrating how to run isolated database tests.

This file shows you how your test database isolation works.
You can run these tests without affecting your production database.
"""

from pathlib import Path

import pytest
from django.conf import settings

from db.core.models import DiscordMember, DiscordReminder


@pytest.mark.django_db()
def test_database_isolation_example() -> None:
    """
    Example test showing database isolation.

    This test demonstrates that:
    1. Each test gets a fresh, empty database
    2. Changes made in one test don't affect other tests
    3. The production database is never touched
    """
    # Verify we're using a test database (pytest-django creates test_* databases or in-memory)
    db_name = settings.DATABASES["default"]["NAME"]
    db_path = Path(str(db_name))
    # For pytest-django, the test database will typically have "test_" prefix or be in-memory
    assert "test_" in str(db_path) or ":memory:" in str(db_name) or "memorydb" in str(db_name)

    # Start with empty database
    assert DiscordMember.objects.count() == 0
    assert DiscordReminder.objects.count() == 0

    # Create test data
    member = DiscordMember.objects.create(discord_id="123456789012345678")
    reminder = DiscordReminder.objects.create(
        discord_member=member,
        message="Test reminder",
        _channel_id="987654321098765432",
        send_datetime="2025-06-25T12:00:00Z",
        _channel_type=0,
    )

    # Verify data was created
    assert DiscordMember.objects.count() == 1
    assert DiscordReminder.objects.count() == 1
    assert reminder.message == "Test reminder"


@pytest.mark.django_db()
def test_second_test_gets_fresh_database() -> None:
    """
    This test demonstrates that each test gets a fresh database.

    Even though the previous test created data, this test starts
    with an empty database because each test gets its own isolated
    temporary database.
    """
    # Database should be empty again for this test
    assert DiscordMember.objects.count() == 0
    assert DiscordReminder.objects.count() == 0

    # We can create different test data without conflicts
    member = DiscordMember.objects.create(discord_id="999888777666555444")

    assert DiscordMember.objects.count() == 1
    assert member.discord_id == "999888777666555444"
