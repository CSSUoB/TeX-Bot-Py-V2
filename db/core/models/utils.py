"""Utility classes and functions."""

from typing import TYPE_CHECKING, override

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django_stubs_ext.db.models import TypedModelMeta

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from collections.abc import Set as AbstractSet
    from typing import ClassVar, Final

    from django.db.models.base import ModelBase

__all__: "Sequence[str]" = ("AsyncBaseModel", "DiscordMember")


class AsyncBaseModel(models.Model):
    """
    Asynchronous base model, defining extra synchronous and asynchronous utility methods.

    This class is abstract so should not be instantiated or have a table made for it in the
    database (see https://docs.djangoproject.com/en/stable/topics/db/models#abstract-base-classes).
    """

    INSTANCES_NAME_PLURAL: str

    class Meta(TypedModelMeta):  # noqa: D106
        abstract: "ClassVar[bool]" = True

    @override
    def __init__(self, *args: object, **kwargs: object) -> None:
        proxy_fields: dict[str, object] = {
            field_name: kwargs.pop(field_name)
            for field_name in set(kwargs.keys()) & self._get_proxy_field_names()
        }

        with transaction.atomic():
            super().__init__(*args, **kwargs)

            field_name: str
            value: object
            for field_name, value in proxy_fields.items():
                setattr(self, field_name, value)

    @override
    def save(
        self,
        *,
        force_insert: bool | tuple["ModelBase", ...] = False,
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
        force_insert: bool | tuple["ModelBase", ...] = False,
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
        for field_name in set(kwargs.keys()) - self._get_proxy_field_names():
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

        with transaction.atomic():
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

    setattr(update, "alters_data", True)  # noqa: B010

    async def aupdate(
        self,
        *,
        commit: bool = True,
        force_insert: bool | tuple["ModelBase", ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: "Iterable[str] | None" = None,
        **kwargs: object,
    ) -> None:
        """
        Asynchronously change an in-memory object's values, then save it to the database.

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

    setattr(aupdate, "alters_data", True)  # noqa: B010

    @classmethod
    def _get_proxy_field_names(cls) -> "AbstractSet[str]":
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
        _("Discord Member ID"),
        unique=True,
        null=False,
        blank=False,
        max_length=20,
        validators=(
            RegexValidator(
                r"\A\d{17,20}\Z",
                "discord_id must be a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)",
            ),
        ),
    )

    @override
    def __str__(self) -> str:
        return self.discord_id

    @override
    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.discord_id!r}>"

    @property
    def member_id(self) -> str:  # noqa: D102
        return self.discord_id

    @member_id.setter
    def member_id(self, value: str | int) -> None:
        self.discord_id = str(value)

    @classmethod
    @override
    def _get_proxy_field_names(cls) -> "AbstractSet[str]":
        return {*super()._get_proxy_field_names(), "member_id"}
