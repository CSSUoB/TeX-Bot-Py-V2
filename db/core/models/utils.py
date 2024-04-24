"""Utility classes & functions."""

from collections.abc import Iterable, Sequence

__all__: Sequence[str] = ("AsyncBaseModel", "HashedDiscordMember")

import hashlib
import re
from typing import Final

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

    INSTANCES_NAME_PLURAL: str

    class Meta:
        """Metadata options about this model."""

        abstract = True

    def save(self, *, force_insert: bool = False, force_update: bool = False, using: str | None = None, update_fields: Iterable[str] | None = None) -> None:  # type: ignore[override] # noqa: E501
        """
        Save the current instance to the database, only after the model has been cleaned.

        Cleaning the model ensures all data in the database is valid, even if the data was not
        added via a ModelForm (E.g. data is added using the ORM API).

        The 'force_insert' and 'force_update' parameters can be used
        to insist that the "save" must be an SQL insert or update
        (or equivalent for non-SQL backends), respectively.
        Normally, they should not be set.
        """
        self.full_clean()

        return super().save(force_insert, force_update, using, update_fields)

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize a new model instance, capturing any proxy field values."""
        proxy_fields: dict[str, object] = {
            field_name: kwargs.pop(field_name)
            for field_name
            in set(kwargs.keys()) & self.get_proxy_field_names()
        }

        super().__init__(*args, **kwargs)

        field_name: str
        value: object
        for field_name, value in proxy_fields.items():
            setattr(self, field_name, value)

    def update(self, *, commit: bool = True, force_insert: bool = False, force_update: bool = False, using: str | None = None, update_fields: Iterable[str] | None = None, **kwargs: object) -> None:  # noqa: E501
        """
        Change an in-memory object's values, then save it to the database.

        This simplifies the two steps into a single operation
        (based on Django's Queryset.bulk_update method).

        The 'force_insert' and 'force_update' parameters can be used
        to insist that the "save" must be an SQL insert or update
        (or equivalent for non-SQL backends), respectively.
        Normally, they should not be set.
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
            UNEXPECTED_KWARGS_MESSAGE: Final[str] = (
                f"{self._meta.model.__name__} got unexpected keyword arguments: "
                f"{tuple(unexpected_kwargs)}"
            )
            raise TypeError(UNEXPECTED_KWARGS_MESSAGE)

        value: object
        for field_name, value in kwargs.items():
            setattr(self, field_name, value)

        if commit:
            return self.save(
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
            )

        return None

    update.alters_data: bool = True  # type: ignore[attr-defined, misc]

    # noinspection SpellCheckingInspection
    async def aupdate(self, *, commit: bool = True, force_insert: bool = False, force_update: bool = False, using: str | None = None, update_fields: Iterable[str] | None = None, **kwargs: object) -> None:  # noqa: E501
        """
        Asyncronously change an in-memory object's values, then save it to the database.

        This simplifies the two steps into a single operation
        (based on Django's Queryset.bulk_update method).

        The 'force_insert' and 'force_update' parameters can be used
        to insist that the "save" must be an SQL insert or update
        (or equivalent for non-SQL backends), respectively.
        Normally, they should not be set.
        """
        await sync_to_async(self.update)(
            commit=commit,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            **kwargs,
        )

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
    Abstract base model to represent a Discord guild member.

    The Discord guild member is identified by their hashed Discord member ID.
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
                "hashed_member_id must be a valid sha256 hex-digest.",
            ),
        ],
    )

    class Meta:
        """Metadata options about this model."""

        abstract: bool = True

    def __str__(self) -> str:
        """Generate the string representation of a generic HashedDiscordMember."""
        return f"{self.hashed_member_id}"

    def __repr__(self) -> str:
        """Generate a developer-focused representation of the hashed discord member's ID."""
        return f"<{self._meta.verbose_name}: {self.hashed_member_id!r}>"

    def __setattr__(self, name: str, value: object) -> None:
        """Set the attribute name to the given value, with special cases for proxy fields."""
        if name == "member_id":
            if not isinstance(value, str | int):
                MEMBER_ID_INVALID_TYPE_MESSAGE: Final[str] = (
                    "member_id must be an instance of str or int."
                )
                raise TypeError(MEMBER_ID_INVALID_TYPE_MESSAGE)

            self.hashed_member_id = self.hash_member_id(value)

        else:
            super().__setattr__(name, value)

    @classmethod
    def hash_member_id(cls, member_id: str | int) -> str:
        """
        Hash the provided member_id.

        The member_id value is hashed into the format that hashed_member_ids are stored in the
        database when new objects of this class are created.
        """
        if not re.match(r"\A\d{17,20}\Z", str(member_id)):
            INVALID_MEMBER_ID_MESSAGE: Final[str] = (
                f"{member_id!r} is not a valid Discord member ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
            )
            raise ValueError(INVALID_MEMBER_ID_MESSAGE)

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
