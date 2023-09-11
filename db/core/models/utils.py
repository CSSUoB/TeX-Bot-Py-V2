"""Utility classes & functions."""

import hashlib
import re
from typing import Any

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist
from django.core.validators import RegexValidator
from django.db import models


class AsyncBaseModel(models.Model):
    """
    Asynchronous base model, defining extra synchronous & asynchronous utility methods.

    This class is abstract so should not be instantiated or have a table made for it in the
    database (see https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    class Meta:
        """Metadata options about this model."""

        abstract = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize a new model instance, capturing any proxy field values."""
        proxy_fields: dict[str, Any] = {
            field_name: kwargs.pop(field_name)
            for field_name
            in set(kwargs.keys()) & self.get_proxy_field_names()
        }

        super().__init__(*args, **kwargs)

        field_name: str
        value: Any
        for field_name, value in proxy_fields.items():
            setattr(self, field_name, value)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the current instance to the database, only after the model has been cleaned.

        Cleaning the model ensures all data in the database is valid, even if the data was not
        added via a ModelForm (E.g. data is added using the ORM API).
        """
        self.full_clean()

        super().save(*args, **kwargs)

    def update(self, commit: bool = True, using: str | None = None, **kwargs: Any) -> None:
        """
        Change an in-memory object's values, then save it to the database.

        This simplifies the two steps into a single operation
        (based on Django's Queryset.bulk_update method).
        """
        unexpected_kwargs: set[str] = set()

        field_name: str
        for field_name in set(kwargs.keys()) - self.get_proxy_field_names():
            try:
                # noinspection PyUnresolvedReferences
                self._meta.get_field(field_name)
            except FieldDoesNotExist:
                unexpected_kwargs.add(field_name)

        if unexpected_kwargs:
            raise TypeError(
                f"{self._meta.model.__name__} got unexpected keyword arguments:"
                f" {tuple(unexpected_kwargs)}"
            )

        value: Any
        for field_name, value in kwargs.items():
            setattr(self, field_name, value)

        if commit:
            self.save(using)

    update.alters_data: bool = True  # type: ignore[attr-defined, misc]

    # noinspection SpellCheckingInspection
    async def aupdate(self, commit: bool = True, using: str | None = None, **kwargs: Any) -> None:  # noqa: E501
        """
        Asyncronously change an in-memory object's values, then save it to the database.

        This simplifies the two steps into a single operation
        (based on Django's Queryset.bulk_update method).
        """
        await sync_to_async(self.update)(commit=commit, using=using, **kwargs)

    aupdate.alters_data: bool = True  # type: ignore[attr-defined, misc]

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
        Return the set of extra names of properties that can be saved to the database.

        These are proxy fields because their values are not stored as object attributes,
        however, they can be used as a reference to a real attribute when saving objects to the
        database.
        """
        return set()


class HashedDiscordMember(AsyncBaseModel):
    """
    Abstract base model to represent a Discord server member.

    The Discord server member is identified by their hashed Discord member ID.
    This base model is inherited by any other model that wishes to store that a Discord member
    had an event happen to them.

    This class is abstract so should not be instantiated or have a table made for it in the
    database (see https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

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
        """Metadata options about this model."""

        abstract: bool = True

    def __repr__(self) -> str:
        """Generate a developer-focused representation of the hashed discord member's ID."""
        return f"<{self._meta.verbose_name}: \"{self.hashed_member_id}\">"

    def __setattr__(self, name: str, value: Any) -> None:
        """Set the attribute name to the given value, with special cases for proxy fields."""
        if name == "member_id":
            self.hashed_member_id = self.hash_member_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        """Generate the string representation of a generic HashedDiscordMember."""
        return f"{self.hashed_member_id}"

    @staticmethod
    def hash_member_id(member_id: Any) -> str:
        """
        Hash the provided member_id.

        The member_id value is hashed into the format that hashed_member_ids are stored in the
        database when new objects of this class are created.
        """
        def is_valid_member_id(value: str | int) -> bool:
            """Validate whether the provided value is a valid Discord member ID."""
            return bool(re.match(r"\A\d{17,20}\Z", str(value)))

        if not isinstance(member_id, (str, int)) or not is_valid_member_id(member_id):
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
        return super().get_proxy_field_names() | {"member_id"}
