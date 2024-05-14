"""Model classes that store extra information between individual event handling call-backs."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "IntroductionReminderOptOutMember",
    "SentOneOffIntroductionReminderMember",
    "SentGetRolesReminderMember",
    "GroupMadeMember",
    "DiscordReminder",
    "LeftDiscordMember",
    "DiscordMemberStrikes",
)


import hashlib
import re
from typing import Final

import discord
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .utils import AsyncBaseModel, HashedDiscordMember


class Action(HashedDiscordMember):
    """Model to represent an action item that has been assigned to a Discord Member."""

    INSTANCES_NAME_PLURAL: str = "Actions"

    hashed_member_id = models.CharField(
        "Hashed Discord Member ID",
        null=False,
        blank=False,
        max_length=64,
        validators=[
            RegexValidator(
                r"\A[A-Fa-f0-9]{64}\Z",
                "hashed_member_id must be a valid sha256 hex-digest.",
            ),
        ],
    )
    description = models.TextField(
        "Description of the action",
        max_length=1500,
        null=False,
        blank=True,
    )
    class Meta:
        verbose_name = "An Action for a Discord Member"
        verbose_name_plural = "Actions for Discord Members"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["hashed_member_id", "description"],
                name="unique_user_action",
            ),
        ]

    def __repr__(self) -> str:
        """Generate a developer-focused representation of this DiscordReminder's attributes."""
        return (
            f"<{self._meta.verbose_name}: {self.hashed_member_id!r}, {str(self.description)!r}"
        )

    def __str__(self) -> str:
        """Generate the string representation of this DiscordReminder."""
        construct_str: str = f"{self.hashed_member_id}"

        if self.description:
            construct_str += f": {self.description[:50]}"

        return construct_str

    def get_formatted_message(self, user_mention: str | None) -> str:
        """
        Return the formatted description stored by this action.

        Adds a mention to the Discord member that was assigned the action,
        if passed in from the calling context.
        """
        constructed_message: str = "This is your reminder"

        if user_mention:
            constructed_message += f", {user_mention}"

        constructed_message += "!"

        if self.description:
            constructed_message = f"**{constructed_message}**\n{self.description}"

        return constructed_message

class IntroductionReminderOptOutMember(HashedDiscordMember):
    """
    Model to represent a Discord member that has opted out of introduction reminders.

    Opting-out of introduction reminders means that they have requested to not be sent any
    messages reminding them to introduce themselves in your group's Discord guild.
    The Discord member is identified by their hashed Discord member ID.
    """

    INSTANCES_NAME_PLURAL: str = "Introduction Reminder Opt-Out Member objects"

    class Meta:  # noqa: D106
        verbose_name = (
            "Hashed Discord ID of a Discord Member "
            "that has Opted-Out of Introduction Reminders"
        )
        verbose_name_plural = (
            "Hashed Discord IDs of Discord Members "
            "that have Opted-Out of Introduction Reminders"
        )


class SentOneOffIntroductionReminderMember(HashedDiscordMember):
    """
    Represents a Discord member that has been sent a one-off introduction reminder.

    A one-off introduction reminder sends a single message
    reminding the Discord member to introduce themselves in your group's Discord guild,
    when SEND_INTRODUCTION_REMINDERS is set to "Once".
    The Discord member is identified by their hashed Discord member ID.
    """

    INSTANCES_NAME_PLURAL: str = "Sent One Off Introduction Reminder Member objects"

    class Meta:  # noqa: D106
        verbose_name = (
            "Hashed Discord ID of a Discord Member "
            "that has had a one-off Introduction reminder sent to their DMs"
        )
        verbose_name_plural = (
            "Hashed Discord IDs of Discord Members "
            "that have had a one-off Introduction reminder sent to their DMs"
        )


class SentGetRolesReminderMember(HashedDiscordMember):
    """
    Represents a Discord member that has already been sent an opt-in roles reminder.

    The opt-in roles reminder suggests to the Discord member to visit the #roles channel
    to claim some opt-in roles within your group's Discord guild.
    The Discord member is identified by their hashed Discord member ID.

    Storing this prevents Discord members from being sent the same reminder to get their
    opt-in roles multiple times, even if they have still not yet got their opt-in roles.
    """

    INSTANCES_NAME_PLURAL: str = "Sent Get Roles Reminder Member objects"

    class Meta:  # noqa: D106
        verbose_name = (
            "Hashed Discord ID of a Discord Member that has had a \"Get Roles\" reminder "
            "sent to their DMs"
        )
        verbose_name_plural = (
            "Hashed Discord IDs of Discord Members that have had a \"Get Roles\" reminder "
            "sent to their DMs"
        )


class GroupMadeMember(AsyncBaseModel):
    """
    Represents a Discord member that has successfully been given the Member role.

    The group member is identified by their hashed group ID.
    If your group stores your members-list on the Guild of students website,
    the hashed group IDs will be hashed UoB IDs.

    Storing the successfully made members prevents multiple people from getting the Member role
    using the same purchased group membership.
    """

    INSTANCES_NAME_PLURAL: str = "Group Made Members"

    hashed_group_member_id = models.CharField(
        "Hashed Group Member ID",
        unique=True,
        null=False,
        blank=False,
        max_length=64,
        validators=[
            RegexValidator(
                r"\A[A-Fa-f\d]{64}\Z",
                "hashed_group_member_id must be a valid sha256 hex-digest.",
            ),
        ],
    )

    class Meta:  # noqa: D106
        verbose_name = "Hashed Group ID of User that has been made Member"
        verbose_name_plural = "Hashed Group IDs of Users that have been made Member"

    def __repr__(self) -> str:
        """Generate a developer-focused representation of the member's hashed Group ID."""
        return f"<{self._meta.verbose_name}: {self.hashed_group_member_id!r}>"

    def __setattr__(self, name: str, value: object) -> None:
        """Set the attribute name to the given value, with special cases for proxy fields."""
        if name == "group_member_id":
            if not isinstance(value, str | int):
                INVALID_GROUP_MEMBER_ID_TYPE_MESSAGE: Final[str] = (
                    "group_member_id must be an instance of str or int."
                )

                raise TypeError(INVALID_GROUP_MEMBER_ID_TYPE_MESSAGE)

            self.hashed_group_member_id = self.hash_group_member_id(value)

        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        """Generate the string representation of this GroupMadeMember."""
        return f"{self.hashed_group_member_id}"

    @staticmethod
    def hash_group_member_id(group_member_id: str | int, group_member_id_type: str = "community group") -> str:  # noqa: E501
        """
        Hash the provided group_member_id.

        The group_member_id value is hashed into the format
        that hashed_group_member_ids are stored in the database
        when new GroupMadeMember objects are created.
        """
        if not re.match(r"\A\d{7}\Z", str(group_member_id)):
            INVALID_GROUP_MEMBER_ID_MESSAGE: Final[str] = (
                f"{group_member_id!r} is not a valid {group_member_id_type} ID."
            )
            raise ValueError(INVALID_GROUP_MEMBER_ID_MESSAGE)

        return hashlib.sha256(str(group_member_id).encode()).hexdigest()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
        Return the set of extra names of properties that can be saved to the database.

        These are proxy fields because their values are not stored as object attributes,
        however, they can be used as a reference to a real attribute when saving objects to the
        database.
        """
        return super().get_proxy_field_names() | {"group_member_id"}


class DiscordReminder(HashedDiscordMember):
    """Represents a reminder that a Discord member has requested to be sent to them."""

    INSTANCES_NAME_PLURAL: str = "Reminders"

    hashed_member_id = models.CharField(
        "Hashed Discord Member ID",
        null=False,
        blank=False,
        max_length=64,
        validators=[
            RegexValidator(
                r"\A[A-Fa-f0-9]{64}\Z",
                "hashed_member_id must be a valid sha256 hex-digest.",
            ),
        ],
    )
    message = models.TextField(
        "Message to remind User",
        max_length=1500,
        null=False,
        blank=True,
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
                "channel_id must be a valid Discord channel ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)",
            ),
        ],
    )
    _channel_type = models.IntegerField(
        "Discord Channel Type of the channel that the reminder needs to be sent in",
        choices=[
            (channel_type.value, channel_type.name)
            for channel_type
            in discord.ChannelType
        ],
        null=True,
        blank=True,
    )
    send_datetime = models.DateTimeField(
        "Date & time to send reminder",
        unique=False,
        null=False,
        blank=False,
    )

    @property
    def channel_id(self) -> int:
        """The ID of the channel that the reminder needs to be sent in."""
        return int(self._channel_id)

    @channel_id.setter
    def channel_id(self, channel_id: str | int) -> None:
        self._channel_id = str(channel_id)

    @property
    def channel_type(self) -> discord.ChannelType:
        """The type of channel that the reminder needs to be sent in."""
        return discord.ChannelType(self._channel_type)

    @channel_type.setter
    def channel_type(self, channel_type: discord.ChannelType | int) -> None:
        if isinstance(channel_type, discord.ChannelType):
            try:
                channel_type = int(channel_type.value)
            except ValueError:
                INVALID_CHANNEL_TYPE_MESSAGE: Final[str] = (
                    "channel_type must be an integer or an instance of discord.ChannelType."
                )
                raise TypeError(INVALID_CHANNEL_TYPE_MESSAGE) from None

        self._channel_type = channel_type

    class Meta:  # noqa: D106
        verbose_name = "A Reminder for a Discord Member"
        verbose_name_plural = "Reminders for Discord Members"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["hashed_member_id", "message", "_channel_id"],
                name="unique_user_channel_message",
            ),
        ]

    def __repr__(self) -> str:
        """Generate a developer-focused representation of this DiscordReminder's attributes."""
        return (
            f"<{self._meta.verbose_name}: {self.hashed_member_id!r}, "
            f"{str(self.channel_id)!r}, {str(self.send_datetime)!r}>"
        )

    def __str__(self) -> str:
        """Generate the string representation of this DiscordReminder."""
        construct_str: str = f"{self.hashed_member_id}"

        if self.message:
            construct_str += f": {self.message[:50]}"

        return construct_str

    def get_formatted_message(self, user_mention: str | None) -> str:
        """
        Return the formatted message stored by this reminder.

        Adds a mention to the Discord member that requested the reminder,
        if passed in from the calling context.
        """
        constructed_message: str = "This is your reminder"

        if user_mention:
            constructed_message += f", {user_mention}"

        constructed_message += "!"

        if self.message:
            constructed_message = f"**{constructed_message}**\n{self.message}"

        return constructed_message

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
        Return the set of extra names of properties that can be saved to the database.

        These are proxy fields because their values are not stored as object attributes,
        however, they can be used as a reference to a real attribute when saving objects to the
        database.
        """
        return super().get_proxy_field_names() | {"channel_id", "channel_type"}


class LeftDiscordMember(AsyncBaseModel):
    """
    Represents a list of roles that a member had when they left your group's Discord guild.

    Storing this allows the stats commands to calculate which roles were most often held by
    Discord members when they left your group's Discord guild.
    """

    INSTANCES_NAME_PLURAL: str = "Left Discord Member objects"

    _roles = models.JSONField("List of roles a Discord Member had")

    @property
    def roles(self) -> set[str]:
        """Retrieve the set of roles the member had when they left your Discord guild."""
        return set(self._roles)

    @roles.setter
    def roles(self, roles: set[str]) -> None:
        self._roles = list(roles)

    class Meta:  # noqa: D106
        verbose_name = (
            "A List of Roles that a Discord Member had "
            "when they left your group's Discord guild"
        )
        verbose_name_plural = (
            "Lists of Roles that Discord Members had when "
            "they left your group's Discord guild"
        )

    def clean(self) -> None:
        """
        Perform extra model-wide validation.

        This runs after clean() has been called on every field by self.clean_fields.
        """
        if any(not isinstance(role, str) for role in self.roles):
            raise ValidationError(
                {
                    "_roles": "Roles must be a set of strings representing the role names.",
                },
                code="invalid",
            )

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
        Return the set of extra names of properties that can be saved to the database.

        These are proxy fields because their values are not stored as object attributes,
        however, they can be used as a reference to a real attribute when saving objects to the
        database.
        """
        return super().get_proxy_field_names() | {"roles"}


class DiscordMemberStrikes(HashedDiscordMember):
    """
    Represents a Discord member that has been given one or more strikes.

    Being given a strike indicates that the Discord member has previously broken one or
    more of your group's Discord guild rules, which resulted in a moderation action being taken
    against them.

    Storing the number of strikes a Discord member has allows future moderation actions
    to be given with increasing severity (as outlined in your group's Discord guild
    moderation document).
    """

    INSTANCES_NAME_PLURAL: str = "Discord Member's Strikes"

    strikes = models.PositiveIntegerField(
        "Number of strikes",
        null=False,
        blank=True,
        validators=[MinValueValidator(0)],
        default=0,
    )

    class Meta:  # noqa: D106
        verbose_name = (
            "Hashed Discord ID of a Discord Member "
            "that has been previously given one or more strikes "
            "because they broke one or more of your group's Discord guild rules"
        )
        verbose_name_plural = (
            "Hashed Discord IDs of Discord Members "
            "that have been previously given one or more strikes "
            "because they broke one or more of your group's Discord guild rules"
        )
