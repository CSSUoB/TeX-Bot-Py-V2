import datetime
import hashlib
import re
from typing import Any

from django.core.validators import RegexValidator  # type: ignore
from django.db import models  # type: ignore

from .utils import Async_Base_Model


class Interaction_Reminder_Opt_Out_Member(Async_Base_Model):
    hashed_member_id: str = models.CharField(
        "Hashed Discord Member ID",
        unique=True,
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

    class Meta:
        verbose_name = "Hashed Discord ID of Member that has Opted-Out of Interaction Reminders"

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: \"{self.hashed_member_id}\">"

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "member_id":
            self.hashed_member_id = self.hash_member_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        return f"{self.hashed_member_id}"

    @staticmethod
    def hash_member_id(member_id: str | int) -> str:
        if not re.match(r"\A\d{17,20}\Z", str(member_id)):
            raise ValueError(f"\"{member_id}\" is not a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)")

        return hashlib.sha256(str(member_id).encode()).hexdigest()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return super().get_proxy_field_names() | {"member_id"}


class UoB_Made_Member(Async_Base_Model):
    hashed_uob_id: str = models.CharField(
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
    def hash_uob_id(uob_id: str) -> str:
        if not re.match(r"\A\d{7}\Z", str(uob_id)):
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


class Discord_Reminder(Async_Base_Model):
    class ChannelType(models.IntegerChoices):
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

    hashed_member_id: str = models.CharField(
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
    message: str | None = models.TextField(
        "Message to remind User",
        max_length=1500,
        null=False,
        blank=True
    )
    _channel_id: str = models.CharField(
        "Discord Channel ID Reminder needs to be sent in",
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
    channel_type: ChannelType = models.IntegerField(
        "Discord Channel Type Reminder needs to be sent in",
        choices=ChannelType.choices,
        null=True,
        blank=True
    )
    send_datetime: datetime.datetime = models.DateTimeField(
        "Date & time to send Reminder at",
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
        verbose_name = "A Reminder for a Discord User."
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
        constructed_message: str = "This is your reminder"

        if user_mention:
            constructed_message += f", {user_mention}"

        constructed_message += "!"

        if self.message:
            constructed_message = f"""**{constructed_message}**\n{self.message}"""

        return constructed_message

    @staticmethod
    def hash_member_id(member_id: str | int) -> str:
        if not re.match(r"\A\d{17,20}\Z", str(member_id)):
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


class Sent_Get_Roles_Reminder_Member(Async_Base_Model):
    hashed_member_id: str = models.CharField(
        "Hashed Discord Member ID",
        unique=True,
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

    class Meta:
        verbose_name = "Hashed Discord ID of Member that has had a \"Get Roles\" Reminder sent to their DMs"

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: \"{self.hashed_member_id}\">"

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "member_id":
            self.hashed_member_id = self.hash_member_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        return f"{self.hashed_member_id}"

    @staticmethod
    def hash_member_id(member_id: str | int) -> str:
        if not re.match(r"\A\d{17,20}\Z", str(member_id)):
            raise ValueError(f"\"{member_id}\" is not a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)")

        return hashlib.sha256(str(member_id).encode()).hexdigest()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return super().get_proxy_field_names() | {"member_id"}
