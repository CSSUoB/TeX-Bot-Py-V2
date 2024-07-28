"""Utility classes & functions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("AsyncBaseModel", "DiscordMember", "BaseDiscordMemberWrapper")


import hashlib
import re
from collections.abc import Iterable
from typing import Final, Never, NoReturn, override

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist
from django.core.validators import RegexValidator
from django.db import models

from .managers import HashedDiscordMemberManager, RelatedDiscordMemberManager


class AsyncBaseModel(models.Model):
    """
    Asynchronous base model, defining extra synchronous & asynchronous utility methods.

    This class is abstract so should not be instantiated or have a table made for it in the
    database (see https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    INSTANCES_NAME_PLURAL: str

    class Meta:  # noqa: D106
        abstract = True

    @override
    def save(self, *, force_insert: bool = False, force_update: bool = False, using: str | None = None, update_fields: Iterable[str] | None = None) -> None:  # type: ignore[override] # noqa: E501
        self.full_clean()

        return super().save(force_insert, force_update, using, update_fields)

    @override
    def __init__(self, *args: object, **kwargs: object) -> None:
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


class DiscordMember(AsyncBaseModel):
    """
    Common model to represent a Discord guild member.

    Instances of this model are related to other models to store information
    about reminders, opt-in/out states, tracked committee actions, etc.

    The Discord guild member is identified by their hashed Discord member ID.
    """

    hashed_discord_id = models.CharField(
        "Hashed Discord Member ID",
        unique=True,
        null=False,
        blank=False,
        max_length=64,
        validators=[
            RegexValidator(
                r"\A[A-Fa-f0-9]{64}\Z",
                "hashed_discord_id must be a valid sha256 hex-digest.",
            ),
        ],
    )

    objects = HashedDiscordMemberManager()

    @override
    def __str__(self) -> str:
        return f"{self.hashed_discord_id}"

    @override
    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.hashed_discord_id!r}>"

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name in ("discord_id", "member_id"):
            if not isinstance(value, str | int):
                MEMBER_ID_INVALID_TYPE_MESSAGE: Final[str] = (
                    f"{name} must be an instance of str or int."
                )
                raise TypeError(MEMBER_ID_INVALID_TYPE_MESSAGE)

            self.hashed_discord_id = self.hash_discord_id(value)
            return

        super().__setattr__(name, value)

    @property
    def discord_id(self) -> NoReturn:
        """Return the Discord ID of this member."""
        HASHED_ID_CANNOT_BE_REVERSED_ERROR_MESSAGE: Final[str] = (
            "The Discord IDs of members are hashed before being sent into the database. "
            "The raw IDs cannot be retrieved after this hashing process."
        )
        raise ValueError(HASHED_ID_CANNOT_BE_REVERSED_ERROR_MESSAGE)

    @property
    def member_id(self) -> NoReturn:
        """Return the Discord ID of this member."""
        return self.discord_id  # type: ignore[misc]

    @property
    def hashed_member_id(self) -> NoReturn:
        """Return the hashed Discord ID of this member."""
        raise DeprecationWarning

    @hashed_member_id.setter
    def hashed_member_id(self, value: Never) -> None:  # noqa: ARG002
        """Assign the hashed Discord ID of this member."""
        raise DeprecationWarning

    @classmethod
    def hash_member_id(cls, member_id: Never) -> NoReturn:  # noqa: ARG003
        """
        Hash the provided discord_id.

        The member_id value is hashed
        into the format that hashed_discord_ids are stored in the database
        when new objects of this class are created.
        """
        raise DeprecationWarning

    @classmethod
    def hash_discord_id(cls, discord_id: str | int) -> str:
        """
        Hash the provided discord_id.

        The discord_id value is hashed
        into the format that hashed_discord_ids are stored in the database
        when new objects of this class are created.
        """
        if not re.fullmatch(r"\A\d{17,20}\Z", str(discord_id)):
            INVALID_MEMBER_ID_MESSAGE: Final[str] = (
                f"{discord_id!r} is not a valid Discord member ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
            )
            raise ValueError(INVALID_MEMBER_ID_MESSAGE)

        return hashlib.sha256(str(discord_id).encode()).hexdigest()

    @classmethod
    @override
    def get_proxy_field_names(cls) -> set[str]:
        return super().get_proxy_field_names() | {"discord_id", "member_id"}


class BaseDiscordMemberWrapper(AsyncBaseModel):
    """
    Abstract base class to wrap more information around a DiscordMember instance.

    This class is abstract so should not be instantiated or have a table made for it in the
    database (see https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    discord_member: DiscordMember

    objects = RelatedDiscordMemberManager()

    class Meta:  # noqa: D106
        abstract = True

    @override
    def __str__(self) -> str:
        return str(self.discord_member)

    @override
    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.discord_member}>"
