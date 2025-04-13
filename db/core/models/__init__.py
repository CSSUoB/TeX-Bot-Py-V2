"""Model classes that store extra information between individual event handling call-backs."""

import hashlib
import re
from typing import TYPE_CHECKING, override

import discord
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .utils import AsyncBaseModel, BaseDiscordMemberWrapper, DiscordMember

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

__all__: "Sequence[str]" = (
    "AssignedCommitteeAction",
    "DiscordMember",
    "DiscordMemberStrikes",
    "DiscordReminder",
    "GroupMadeMember",
    "IntroductionReminderOptOutMember",
    "LeftDiscordMember",
    "SentGetRolesReminderMember",
    "SentOneOffIntroductionReminderMember",
)


class AssignedCommitteeAction(BaseDiscordMemberWrapper):
    """Model to represent an action that has been assigned to a Discord committee-member."""

    class Status(models.TextChoices):
        """The named status and shortcode associated with the progress of each action."""

        BLOCKED = "BLK", _("Blocked")
        CANCELLED = "CND", _("Cancelled")
        COMPLETE = "CMP", _("Complete")
        IN_PROGRESS = "INP", _("In Progress")
        NOT_STARTED = "NST", _("Not Started")

    INSTANCES_NAME_PLURAL: str = "Assigned Committee Actions"

    discord_member = models.ForeignKey(  # type: ignore[assignment]
        DiscordMember,
        on_delete=models.CASCADE,
        related_name="assigned_committee_actions",
        verbose_name="Discord Member",
        blank=False,
        null=False,
        unique=False,
    )
    description = models.TextField(
        "Description",
        max_length=200,
        null=False,
        blank=False,
    )
    status = models.CharField(
        max_length=3,
        choices=Status,
        default=Status.NOT_STARTED,
        null=False,
        blank=False,
    )

    class Meta:  # noqa: D106
        verbose_name = "Assigned Committee Action"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["discord_member", "description"],
                name="unique_user_action",
            ),
        ]

    @override
    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.discord_member}, {self.description}"  # type: ignore[has-type]

    @override
    def __str__(self) -> str:
        return f"{self.discord_member}: {self.description}"  # type: ignore[has-type]


class IntroductionReminderOptOutMember(BaseDiscordMemberWrapper):
    """
    Model to represent a Discord member that has opted out of introduction reminders.

    Opting-out of introduction reminders means that they have requested to not be sent any
    messages reminding them to introduce themselves in your group's Discord guild.
    """

    INSTANCES_NAME_PLURAL: str = "Introduction Reminder Opt-Out Member objects"

    discord_member = models.OneToOneField(  # type: ignore[assignment]
        DiscordMember,
        on_delete=models.CASCADE,
        related_name="opted_out_of_introduction_reminders",
        verbose_name="Discord Member",
        blank=False,
        null=False,
        primary_key=True,
    )

    class Meta:  # noqa: D106
        verbose_name = "Discord Member that has Opted-Out of Introduction Reminders"
        verbose_name_plural = "Discord Members that have Opted-Out of Introduction Reminders"


class SentOneOffIntroductionReminderMember(BaseDiscordMemberWrapper):
    """
    Represents a Discord member that has been sent a one-off introduction reminder.

    A one-off introduction reminder sends a single message
    reminding the Discord member to introduce themselves in your group's Discord guild,
    when SEND_INTRODUCTION_REMINDERS is set to "Once".
    """

    INSTANCES_NAME_PLURAL: str = "Sent One-Off Introduction Reminder Member objects"

    discord_member = models.OneToOneField(  # type: ignore[assignment]
        DiscordMember,
        on_delete=models.CASCADE,
        related_name="sent_one_off_introduction_reminder",
        verbose_name="Discord Member",
        blank=False,
        null=False,
        primary_key=True,
    )

    class Meta:  # noqa: D106
        verbose_name = (
            "Discord Member that has had a one-off Introduction reminder sent to their DMs"
        )
        verbose_name_plural = (
            "Discord Members that have had a one-off Introduction reminder sent to their DMs"
        )


class SentGetRolesReminderMember(BaseDiscordMemberWrapper):
    """
    Represents a Discord member that has already been sent an opt-in roles reminder.

    The opt-in roles reminder suggests the Discord member visit the #roles channel
    to claim some opt-in roles within your group's Discord guild.
    The Discord member is identified by their hashed Discord member ID.

    Storing this prevents Discord members from being sent the same reminder to get their
    opt-in roles multiple times, even if they have still not yet got their opt-in roles.
    """

    INSTANCES_NAME_PLURAL: str = "Sent Get Roles Reminder Member objects"

    discord_member = models.OneToOneField(  # type: ignore[assignment]
        DiscordMember,
        on_delete=models.CASCADE,
        related_name="sent_get_roles_reminder",
        verbose_name="Discord Member",
        blank=False,
        null=False,
        primary_key=True,
    )

    class Meta:  # noqa: D106
        verbose_name = 'Discord Member that has had a "Get Roles" reminder sent to their DMs'
        verbose_name_plural = (
            'Discord Members that have had a "Get Roles" reminder sent to their DMs'
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

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "group_member_id":
            if not isinstance(value, str | int):
                INVALID_GROUP_MEMBER_ID_TYPE_MESSAGE: Final[str] = (
                    "group_member_id must be an instance of str or int."
                )

                raise TypeError(INVALID_GROUP_MEMBER_ID_TYPE_MESSAGE)

            self.hashed_group_member_id = self.hash_group_member_id(value)

        else:
            super().__setattr__(name, value)

    @override
    def __str__(self) -> str:
        return f"{self.hashed_group_member_id}"

    @override
    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.hashed_group_member_id!r}>"

    @classmethod
    def hash_group_member_id(
        cls, group_member_id: str | int, group_member_id_type: str = "community group"
    ) -> str:
        """
        Hash the provided group_member_id.

        The group_member_id value is hashed into the format
        that hashed_group_member_ids are stored in the database
        when new GroupMadeMember objects are created.
        """
        if not re.fullmatch(r"\A\d{7}\Z", str(group_member_id)):
            INVALID_GROUP_MEMBER_ID_MESSAGE: Final[str] = (
                f"{group_member_id!r} is not a valid {group_member_id_type} ID."
            )
            raise ValueError(INVALID_GROUP_MEMBER_ID_MESSAGE)

        return hashlib.sha256(str(group_member_id).encode()).hexdigest()

    @classmethod
    @override
    def get_proxy_field_names(cls) -> set[str]:
        return super().get_proxy_field_names() | {"group_member_id"}


class DiscordReminder(BaseDiscordMemberWrapper):
    """Represents a reminder that a Discord member has requested to be sent to them."""

    INSTANCES_NAME_PLURAL: str = "Reminders"

    discord_member = models.ForeignKey(  # type: ignore[assignment]
        DiscordMember,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="Discord Member",
        blank=False,
        null=False,
        unique=False,
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
            (channel_type.value, channel_type.name) for channel_type in discord.ChannelType
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
                fields=["discord_member", "message", "_channel_id"],
                name="unique_user_channel_message",
            ),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"{self.discord_member}"  # type: ignore[has-type]
            f"{
                ''
                if not self.message
                else (f': {self.message[:50]}...' if len(self.message) > 50 else self.message)
            }"
        )

    @override
    def __repr__(self) -> str:
        return (
            f"<{self._meta.verbose_name}: {self.discord_member}, "  # type: ignore[has-type]
            f"{self.channel_id!r}, {self.send_datetime!r}>"
        )

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
    @override
    def get_proxy_field_names(cls) -> set[str]:
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
            "Lists of Roles that Discord Members had when they left your group's Discord guild"
        )

    @override
    def __str__(self) -> str:
        return f"{self.id}: {', '.join(self.roles)}"

    @override
    def __repr__(self) -> str:
        return (
            f"<{self._meta.verbose_name}: {{{', '.join(repr(role) for role in self.roles)}}}>"
        )

    @override
    def clean(self) -> None:
        if any(not isinstance(role, str) for role in self.roles):
            raise ValidationError(
                {
                    "_roles": "Roles must be a set of strings representing the role names.",
                },
                code="invalid",
            )

    @classmethod
    @override
    def get_proxy_field_names(cls) -> set[str]:
        return super().get_proxy_field_names() | {"roles"}


class DiscordMemberStrikes(BaseDiscordMemberWrapper):
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

    discord_member = models.OneToOneField(  # type: ignore[assignment]
        DiscordMember,
        on_delete=models.CASCADE,
        related_name="strikes",
        verbose_name="Discord Member",
        blank=False,
        null=False,
        primary_key=True,
    )
    strikes = models.PositiveIntegerField(
        "Number of strikes",
        null=False,
        blank=True,
        validators=[MinValueValidator(0)],
        default=0,
    )

    class Meta:  # noqa: D106
        verbose_name = (
            "Discord Member that has been previously given one or more strikes "
            "because they broke one or more of your group's Discord guild rules"
        )
        verbose_name_plural = (
            "Discord Members that have been previously given one or more strikes "
            "because they broke one or more of your group's Discord guild rules"
        )

    @override
    def __str__(self) -> str:
        return f"{self.discord_member}: {self.strikes}"  # type: ignore[has-type]

    @override
    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.discord_member}, {self.strikes!r}>"  # type: ignore[has-type]
