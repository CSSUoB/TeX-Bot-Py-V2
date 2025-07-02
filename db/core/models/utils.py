"""Utility classes and functions."""

import re
from typing import TYPE_CHECKING, override

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist
from django.core.validators import RegexValidator
from django.db import models

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import Final

__all__: "Sequence[str]" = ("AsyncBaseModel", "BaseDiscordMemberWrapper", "DiscordMember")


class AsyncBaseModel(models.Model):
    """
    Asynchronous base model, defining extra synchronous and asynchronous utility methods.

    This class is abstract so should not be instantiated or have a table made for it in the
    database (see https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    INSTANCES_NAME_PLURAL: str

    class Meta:  # noqa: D106
        abstract = True

    @override
    def __init__(self, *args: object, **kwargs: object) -> None:
        proxy_fields: dict[str, object] = {
            field_name: kwargs.pop(field_name)
            for field_name in set(kwargs.keys()) & self.get_proxy_field_names()
        }

        super().__init__(*args, **kwargs)

        field_name: str
        value: object
        for field_name, value in proxy_fields.items():
            setattr(self, field_name, value)

    @override
    def save(  # type: ignore[override]
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: "Iterable[str] | None" = None,
    ) -> None:
        self.full_clean()

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def update(
        self,
        *,
        commit: bool = True,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: "Iterable[str] | None" = None,
        **kwargs: object,
    ) -> None:
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

    async def aupdate(
        self,
        *,
        commit: bool = True,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: "Iterable[str] | None" = None,
        **kwargs: object,
    ) -> None:
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

    The Discord guild member is identified by their Discord member ID.
    """

    discord_id = models.CharField(
        "Discord Member ID",
        unique=True,
        null=False,
        blank=False,
        max_length=20,
        validators=[
            RegexValidator(
                r"\A\d{17,20}\Z",
                "discord_id must be a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)",
            ),
        ],
    )

    @override
    def __str__(self) -> str:
        return self.discord_id

    @override
    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.discord_id!r}>"

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name in ("member_id",):
            if not isinstance(value, str | int):
                MEMBER_ID_INVALID_TYPE_MESSAGE: Final[str] = (
                    f"{name} must be an instance of str or int."
                )
                raise TypeError(MEMBER_ID_INVALID_TYPE_MESSAGE)

            self.discord_id = str(value)
            return

        super().__setattr__(name, value)

    @property
    def member_id(self) -> str:
        """Return the Discord ID of this member."""
        return self.discord_id

    @member_id.setter
    def member_id(self, value: str | int) -> None:
        """Set the Discord ID of this member."""
        # Validate Discord ID format
        if not re.fullmatch(r"\A\d{17,20}\Z", str(value)):
            INVALID_MEMBER_ID_MESSAGE: Final[str] = (
                f"{value!r} is not a valid Discord member ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
            )
            raise ValueError(INVALID_MEMBER_ID_MESSAGE)

        self.discord_id = str(value)

    @classmethod
    @override
    def get_proxy_field_names(cls) -> set[str]:
        return super().get_proxy_field_names() | {"member_id"}
