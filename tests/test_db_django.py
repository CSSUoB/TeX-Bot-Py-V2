"""Alternative database test using Django's TestCase for better isolation."""

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from db.core.models import DiscordMember, DiscordReminder


class TestDiscordReminderDjango(TestCase):
    """Test suite for the DiscordReminder class using Django's TestCase."""

    def test_successful_reminder_creation(self) -> None:
        """Test that a DiscordReminder can be created successfully."""
        # First create a DiscordMember (required foreign key)
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        # Create the reminder
        reminder = DiscordReminder.objects.create(
            discord_member=discord_member,
            message="This is a test reminder.",
            _channel_id="987654321098765432",
            send_datetime="2025-06-25T12:00:00Z",
            _channel_type=1,
        )

        # Verify the reminder was created correctly
        assert DiscordReminder.objects.all().count() == 1
        retrieved_reminder = DiscordReminder.objects.get(
            discord_member=discord_member,
        )
        assert retrieved_reminder == reminder
        assert retrieved_reminder.message == "This is a test reminder."
        assert retrieved_reminder.channel_id == 987654321098765432
        # Test the internal field value as well
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

        # Test getter
        assert reminder.channel_id == 123456789012345678
        assert isinstance(reminder.channel_id, int)

        # Test setter
        reminder.channel_id = "987654321098765432"
        assert reminder._channel_id == "987654321098765432"  # noqa: SLF001
        assert reminder.channel_id == 987654321098765432

    def test_reminder_invalid_channel_id(self) -> None:
        """Test that invalid channel IDs raise validation errors."""
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        # Test with invalid channel ID (too short)
        reminder = DiscordReminder(
            discord_member=discord_member,
            message="Test message",
            _channel_id="123",  # Too short
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

        # Verify reminder exists
        assert DiscordReminder.objects.count() == 1

        # Delete the discord member
        discord_member.delete()

        # Verify reminder was also deleted due to CASCADE
        assert DiscordReminder.objects.count() == 0

    def test_multiple_reminders_same_user(self) -> None:
        """Test that a user can have multiple reminders."""
        discord_member = DiscordMember.objects.create(
            discord_id=123456789012345678,
        )

        # Create multiple reminders for the same user
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

        # Verify both reminders exist
        assert DiscordReminder.objects.count() == 2
        assert discord_member.reminders.count() == 2

        # Verify we can retrieve both
        reminders = list(discord_member.reminders.all())
        assert reminder1 in reminders
        assert reminder2 in reminders
