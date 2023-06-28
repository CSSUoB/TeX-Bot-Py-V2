"""
    Model classes that store extra information longer-term between individual
    Discord command events.
"""

import hashlib
import re
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from .utils import AsyncBaseModel, HashedDiscordMember


class IntroductionReminderOptOutMember(HashedDiscordMember):
    """
        Model to represent a Discord server member (identified by their hashed
        Discord member ID) that has requested to be opted-out of reminders to
        introduce themselves in the CSS Discord server.
    """

    class Meta:
        verbose_name = "Hashed Discord ID of Member that has Opted-Out of Introduction Reminders"


class SentOneOffIntroductionReminderMember(HashedDiscordMember):
    """
        Model to represent a Discord server member (identified by their hashed
        Discord member ID) that has already been sent their single reminder to
        introduce themselves in the CSS Discord server, when
        SEND_INTRODUCTION_REMINDERS is set to "Once".
    """

    class Meta:
        verbose_name = "Hashed Discord ID of Member that has had a one-off Introduction reminder sent to their DMs"


class SentGetRolesReminderMember(HashedDiscordMember):
    """
        Model to represent a Discord server member (identified by their hashed
        Discord member ID) that has already been sent a reminder to get their
        opt-in roles within the CSS Discord server.

        Storing this prevents Discord members from being sent the same reminder
        to get their opt-in roles multiple times, even if they have still not
        yet got their opt-in roles.
    """

    class Meta:
        verbose_name = "Hashed Discord ID of Member that has had a \"Get Roles\" reminder sent to their DMs"


class UoBMadeMember(AsyncBaseModel):
    """
        Model to represent a CSS member (identified by their hashed Uob ID) that
        has successfully been given the Member role on the CSS Discord server.

        Storing the successfully made members prevents multiple people from
        getting the Member role using the same purchased society membership.
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
        verbose_name = "Hashed UoB ID of User that has been made Member"

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: \"{self.hashed_uob_id}\">"

    def __setattr__(self, name: str, value: Any):
        if name == "uob_id":
            self.hashed_uob_id = self.hash_uob_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        return f"{self.hashed_uob_id}"

    @staticmethod
    def hash_uob_id(uob_id: Any) -> str:
        """
            Hashes the provided uob_id into the format that hashed_uob_ids
            are stored in the database when new UoBMadeMember objects are
            created.
        """

        if not isinstance(uob_id, (str, int)) or not re.match(r"\A\d{7}\Z", str(uob_id)):
            raise ValueError(f"\"{uob_id}\" is not a valid UoB Student ID.")

        return hashlib.sha256(str(uob_id).encode()).hexdigest()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
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
        return int(self._channel_id)

    @channel_id.setter
    def channel_id(self, channel_id: str | int) -> None:
        self._channel_id = str(channel_id)

    class Meta:
        verbose_name = "A Reminder for a Discord Member."
        constraints = [
            models.UniqueConstraint(
                fields=["hashed_member_id", "message", "_channel_id"],
                name="unique_user_channel_message"
            )
        ]

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: \"{self.hashed_member_id}\", \"{self.channel_id}\", \"{self.send_datetime}\">"

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "member_id":
            self.hashed_member_id = self.hash_member_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        construct_str: str = f"{self.hashed_member_id}"

        if self.message:
            construct_str += f": {self.message[:50]}"

        return construct_str

    def format_message(self, user_mention: str | None) -> str:
        """
            Returns the formatted message stored by this reminder, adds a
            mention to the user that requested the reminder if passed in from
            the calling context.
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
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return super().get_proxy_field_names() | {"member_id", "channel_id"}


class LeftMember(AsyncBaseModel):
    """
        Model to represent a list of roles that a Discord server member had when
        they left the CSS Discord server.

        Storing this allows the stats commands to calculate which roles were
        most often held by Discord members when they left the CSS Discord server.
    """

    _roles = models.JSONField("List of roles a Member had")

    @property
    def roles(self) -> set[str]:
        return set(self._roles)

    @roles.setter
    def roles(self, roles: set[str]) -> None:
        self._roles = list(roles)

    class Meta:
        verbose_name = "A List of Roles that a Member had when they left the CSS Discord server."

    def clean(self) -> None:
        """
            Performs extra model-wide validation after clean() has been called
            on every field by self.clean_fields.
        """

        if any(not isinstance(role, str) for role in self.roles):
            raise ValidationError({"_roles": "Roles must be a set of strings representing the role names."}, code="invalid")

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return super().get_proxy_field_names() | {"roles"}
