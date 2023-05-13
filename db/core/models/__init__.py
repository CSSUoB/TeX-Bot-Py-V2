import hashlib
import re
from typing import Any

from django.core.validators import RegexValidator  # type: ignore
from django.db import models  # type: ignore

from .utils import Async_Base_Model


class Interaction_Reminder_Opt_Out_Member(Async_Base_Model):
    hashed_member_id = models.CharField(
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
