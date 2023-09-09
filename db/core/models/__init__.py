"""Model classes that store extra information between individual event handling call-backs."""

import hashlib
import re
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from .utils import AsyncBaseModel, HashedDiscordMember


class IntroductionReminderOptOutMember(HashedDiscordMember):
    """
    Model to represent a Discord server member that has opted out of introduction reminders.

    Opting-out of introduction reminders means that they have requested to not be sent any
    messages reminding them to introduce themselves in the CSS Discord server.
    The Discord server member is identified by their hashed Discord member ID.
    """

    class Meta:
        """Metadata options about this model."""

        verbose_name = "Hashed Discord ID of Member that has Opted-Out of Introduction Reminders"
        verbose_name_plural = "Hashed Discord IDs of Members that have Opted-Out of Introduction Reminders"


class SentOneOffIntroductionReminderMember(HashedDiscordMember):
    """
    Represents a Discord server member that has been sent a one-off introduction reminder.

    A one-off introduction reminder sends a single message reminding the member to introduce
    themselves in the CSS Discord server, when SEND_INTRODUCTION_REMINDERS is set to "Once".
    The Discord server member is identified by their hashed Discord member ID.
    """

    class Meta:
        """Metadata options about this model."""

        verbose_name = "Hashed Discord ID of Member that has had a one-off Introduction reminder sent to their DMs"
        verbose_name_plural = "Hashed Discord IDs of Members that have had a one-off Introduction reminder sent to their DMs"


class SentGetRolesReminderMember(HashedDiscordMember):
    """
    Represents a Discord server member that has already been sent an opt-in roles reminder.

    The opt-in roles reminder suggests to the member to visit the #roles channel to claim some
    opt-in roles within the CSS Discord server.
    The Discord server member is identified by their hashed Discord member ID.

    Storing this prevents Discord members from being sent the same reminder to get their
    opt-in roles multiple times, even if they have still not yet got their opt-in roles.
    """

    class Meta:
        """Metadata options about this model."""

        verbose_name = "Hashed Discord ID of Member that has had a \"Get Roles\" reminder sent to their DMs"
        verbose_name_plural = "Hashed Discord IDs of Members that have had a \"Get Roles\" reminder sent to their DMs"


class UoBMadeMember(AsyncBaseModel):
    """
    Represents a CSS member that has successfully been given the Member role.

    The CSS member is identified by their hashed UoB ID.

    Storing the successfully made members prevents multiple people from getting the Member role
    using the same purchased society membership.
    """

    hashed_uob_id = models.CharField(
        "Hashed UoB ID",
        unique=True,
        null=False,
        blank=False,
        max_length=64,
        validators=[
            RegexValidator(
                r"\A[A-Fa-f\d]{64}\Z",
                "hashed_uob_id must be a valid sha256 hex-digest."
            )
        ]
    )

    class Meta:
        """Metadata options about this model."""

        verbose_name = "Hashed UoB ID of User that has been made Member"
        verbose_name_plural = "Hashed UoB IDs of Users that have been made Member"

    def __repr__(self) -> str:
        """Generate a developer-focused representation of the member's hashed UoB ID."""
        return f"<{self._meta.verbose_name}: \"{self.hashed_uob_id}\">"

    def __setattr__(self, name: str, value: Any) -> None:
        """Set the attribute name to the given value, with special cases for proxy fields."""
        if name == "uob_id":
            self.hashed_uob_id = self.hash_uob_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        """Generate the string representation of this UoBMadeMember."""
        return f"{self.hashed_uob_id}"

    @staticmethod
    def hash_uob_id(uob_id: Any) -> str:
        """
        Hash the provided uob_id.

        The uob_id value is hashed into the format that hashed_uob_ids are stored in the
        database when new UoBMadeMember objects are created.
        """
        if not isinstance(uob_id, (str, int)) or not re.match(r"\A\d{7}\Z", str(uob_id)):
            raise ValueError(f"\"{uob_id}\" is not a valid UoB Student ID.")

        return hashlib.sha256(str(uob_id).encode()).hexdigest()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
        Return the set of extra names of properties that can be saved to the database.

        These are proxy fields because their values are not stored as object attributes,
        however, they can be used as a reference to a real attribute when saving objects to the
        database.
        """
        return super().get_proxy_field_names() | {"uob_id"}


class DiscordReminder(AsyncBaseModel):
    """
        Model to represent a reminder that a Discord server member has requested
        to be sent in the future.
    """

    class ChannelType(models.IntegerChoices):
        """
            Enum to represent the allowed choices of the channel_type field of a
            DiscordReminder.
        """

        TEXT = 0, "text"
        PRIVATE = 1, "private"
        VOICE = 2, "voice"
        GROUP = 3, "group"
        CATEGORY = 4, "category"
        NEWS = 5, "news"
        NEWS_THREAD = 10, "news_thread"
        PUBLIC_THREAD = 11, "public_thread"
        PRIVATE_THREAD = 12, "private_thread"
        STAGE_VOICE = 13, "stage_voice"
        DIRECTORY = 14, "directory"
        FORUM = 15, "forum"

        def __str__(self) -> str:
            return self.label

    hashed_member_id = models.CharField(
        "Hashed Discord Member ID",
        null=False,
        blank=False,
        max_length=64,
        validators=[
            RegexValidator(
                r"\A[A-Fa-f0-9]{64}\Z",
                "hashed_member_id must be a valid sha256 hex-digest."
            )
        ]
    )
    message = models.TextField(
        "Message to remind User",
        max_length=1500,
        null=False,
        blank=True
    )
    _channel_id = models.CharField(
        "Discord Channel ID of the channel that the reminder needs to be sent in",
        unique=False,
        null=False,
        blank=False,
        max_length=30,
        validators=[
            RegexValidator(
                r"\A\d{17,20}\Z",
                "channel_id must be a valid Discord channel ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
            )
        ]
    )
    channel_type = models.IntegerField(
        "Discord Channel Type of the channel that the reminder needs to be sent in",
        choices=ChannelType.choices,
        null=True,
        blank=True
    )
    send_datetime = models.DateTimeField(
        "Date & time to send reminder",
        unique=False,
        null=False,
        blank=False
    )

    @property
    def channel_id(self) -> int:
        """The ID of the channel that the reminder needs to be sent in."""
        return int(self._channel_id)

    @channel_id.setter
    def channel_id(self, channel_id: str | int) -> None:
        self._channel_id = str(channel_id)

    class Meta:
        """Metadata options about this model."""

        verbose_name = "A Reminder for a Discord Member"
        verbose_name_plural = "Reminders for Discord Members"
        constraints = [
            models.UniqueConstraint(
                fields=["hashed_member_id", "message", "_channel_id"],
                name="unique_user_channel_message"
            )
        ]

    def __repr__(self) -> str:
        """Generate a developer-focused representation of this DiscordReminder's attributes."""
        return f"<{self._meta.verbose_name}: \"{self.hashed_member_id}\", \"{self.channel_id}\", \"{self.send_datetime}\">"

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "member_id":
            self.hashed_member_id = self.hash_member_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        """Generate the string representation of this DiscordReminder."""
        construct_str: str = f"{self.hashed_member_id}"

        if self.message:
            construct_str += f": {self.message[:50]}"

        return construct_str

    def format_message(self, user_mention: str | None) -> str:
        """
        Return the formatted message stored by this reminder.

        Adds a mention to the member that requested the reminder, if passed in from the calling
        context.
        """
        constructed_message: str = "This is your reminder"

        if user_mention:
            constructed_message += f", {user_mention}"

        constructed_message += "!"

        if self.message:
            constructed_message = f"""**{constructed_message}**\n{self.message}"""

        return constructed_message

    @staticmethod
    def hash_member_id(member_id: Any) -> str:
        """
            Hashes the provided member_id into the format that hashed_member_ids
            are stored in the database when new DiscordReminder objects are
            created.
        """

        if not isinstance(member_id, (str, int)) or not re.match(r"\A\d{17,20}\Z", str(member_id)):
            raise ValueError(f"\"{member_id}\" is not a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)")

        return hashlib.sha256(str(member_id).encode()).hexdigest()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
        Return the set of extra names of properties that can be saved to the database.

        These are proxy fields because their values are not stored as object attributes,
        however, they can be used as a reference to a real attribute when saving objects to the
        database.
        """

        return super().get_proxy_field_names() | {"member_id", "channel_id"}


class LeftMember(AsyncBaseModel):
    """
    Represents a list of roles that a member had when they left the CSS Discord server.

    Storing this allows the stats commands to calculate which roles were most often held by
    Discord members when they left the CSS Discord server.
    """

    _roles = models.JSONField("List of roles a Member had")

    @property
    def roles(self) -> set[str]:
        """Retrieve the set of roles the member had when they left the CSS Discord server."""
        return set(self._roles)

    @roles.setter
    def roles(self, roles: set[str]) -> None:
        self._roles = list(roles)

    class Meta:
        """Metadata options about this model."""

        verbose_name = "A List of Roles that a Member had when they left the CSS Discord server"
        verbose_name_plural = "Lists of Roles that Members had when they left the CSS Discord server"

    def clean(self) -> None:
        """
        Perform extra model-wide validation.

        This runs after clean() has been called on every field by self.clean_fields.
        """
        if any(not isinstance(role, str) for role in self.roles):
            raise ValidationError({"_roles": "Roles must be a set of strings representing the role names."}, code="invalid")

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
        Return the set of extra names of properties that can be saved to the database.

        These are proxy fields because their values are not stored as object attributes,
        however, they can be used as a reference to a real attribute when saving objects to the
        database.
        """
        return super().get_proxy_field_names() | {"roles"}
