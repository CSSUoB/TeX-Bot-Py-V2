"""Manager classes used for DB access upon models."""

import abc
import logging
from typing import TYPE_CHECKING, TypeVar, final, override

from django.db.models import Manager

import utils

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping, Sequence
    from logging import Logger
    from typing import Final

    from django.core.exceptions import ObjectDoesNotExist
    from django.db.models import QuerySet

    from .utils import AsyncBaseModel, BaseDiscordMemberWrapper, DiscordMember  # noqa: F401

__all__: "Sequence[str]" = ("HashedDiscordMemberManager", "RelatedDiscordMemberManager")

if TYPE_CHECKING:
    T_model = TypeVar("T_model", bound=AsyncBaseModel)

    T_BaseDiscordMemberWrapper = TypeVar(
        "T_BaseDiscordMemberWrapper", bound=BaseDiscordMemberWrapper
    )

    type Defaults = MutableMapping[str, object | Callable[[], object]] | None


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class BaseHashedIDManager(Manager["T_model"], abc.ABC):
    """Base manager class to remove a given unhashed ID before executing a query."""

    use_in_migrations: bool = True

    # noinspection SpellCheckingInspection
    @abc.abstractmethod
    def _remove_unhashed_id_from_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:
        """Remove any unhashed ID values from the kwargs dict before executing a query."""

    @final
    def _perform_remove_unhashed_id_from_kwargs(
        self, kwargs: dict[str, object]
    ) -> dict[str, object]:
        if utils.is_running_in_async():
            SYNC_IN_ASYNC_MESSAGE: Final[str] = (
                "Synchronous database access used in asynchronous context. "
                "Use the respective async version of this function instead."
            )
            raise RuntimeError(SYNC_IN_ASYNC_MESSAGE)

        return self._remove_unhashed_id_from_kwargs(kwargs=kwargs)

    # noinspection SpellCheckingInspection
    @abc.abstractmethod
    async def _aremove_unhashed_id_from_kwargs(
        self, kwargs: dict[str, object]
    ) -> dict[str, object]:
        """Remove any unhashed_id values from the kwargs dict before executing a query."""

    @override
    def get(self, *args: object, **kwargs: object) -> "T_model":
        return super().get(*args, **self._perform_remove_unhashed_id_from_kwargs(kwargs))

    @override
    async def aget(self, *args: object, **kwargs: object) -> "T_model":
        return await super().aget(
            *args,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def filter(self, *args: object, **kwargs: object) -> "QuerySet[T_model]":
        return super().filter(
            *args,
            **self._perform_remove_unhashed_id_from_kwargs(kwargs),
        )

    async def afilter(self, *args: object, **kwargs: object) -> "QuerySet[T_model]":
        return super().filter(
            *args,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def exclude(self, *args: object, **kwargs: object) -> "QuerySet[T_model]":
        return super().exclude(
            *args,
            **self._perform_remove_unhashed_id_from_kwargs(kwargs),
        )

    # noinspection SpellCheckingInspection
    async def aexclude(self, *args: object, **kwargs: object) -> "QuerySet[T_model]":
        return super().exclude(
            *args,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def create(self, **kwargs: object) -> "T_model":
        return super().create(**self._perform_remove_unhashed_id_from_kwargs(kwargs))

    # noinspection SpellCheckingInspection
    @override
    async def acreate(self, **kwargs: object) -> "T_model":
        return await super().acreate(**(await self._aremove_unhashed_id_from_kwargs(kwargs)))

    @override
    def get_or_create(
        self, defaults: "Defaults" = None, **kwargs: object
    ) -> tuple["T_model", bool]:  # type: ignore[override]
        return super().get_or_create(
            defaults=defaults,
            **self._perform_remove_unhashed_id_from_kwargs(kwargs),
        )

    @override
    async def aget_or_create(
        self, defaults: "Defaults" = None, **kwargs: object
    ) -> tuple["T_model", bool]:  # type: ignore[override]
        return await super().aget_or_create(
            defaults=defaults,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def update_or_create(
        self, defaults: "Defaults" = None, create_defaults: "Defaults" = None, **kwargs: object
    ) -> tuple["T_model", bool]:  # type: ignore[override]
        return super().get_or_create(
            defaults=defaults,
            create_defaults=create_defaults,
            **self._perform_remove_unhashed_id_from_kwargs(kwargs),
        )

    # noinspection SpellCheckingInspection
    @override
    async def aupdate_or_create(
        self, defaults: "Defaults" = None, create_defaults: "Defaults" = None, **kwargs: object
    ) -> tuple["T_model", bool]:  # type: ignore[override]
        return await super().aupdate_or_create(
            defaults=defaults,
            create_defaults=create_defaults,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def update(self, **kwargs: object) -> int:
        return super().update(**self._perform_remove_unhashed_id_from_kwargs(kwargs))

    # noinspection SpellCheckingInspection
    @override
    async def aupdate(self, **kwargs: object) -> int:
        return await super().aupdate(**(await self._aremove_unhashed_id_from_kwargs(kwargs)))


class HashedDiscordMemberManager(BaseHashedIDManager["DiscordMember"]):
    """
    Manager class to create & retrieve DiscordMember model instances.

    This manager implements extra functionality to filter/create instances
    using a given discord_id that with be automatically hashed before saved to the database.
    """

    # noinspection SpellCheckingInspection
    @override
    def _remove_unhashed_id_from_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:
        raw_discord_id: object | None = None

        field_name: str
        for field_name in ("discord_id", "member_id"):
            if not raw_discord_id:
                raw_discord_id = kwargs.pop(field_name, None)
            else:
                kwargs.pop(field_name, None)

        if not isinstance(raw_discord_id, int | str | None):
            raise TypeError

        discord_id: int | str | None = raw_discord_id

        if discord_id:
            kwargs["hashed_discord_id"] = self.model.hash_discord_id(discord_id)

        return kwargs

    # noinspection SpellCheckingInspection
    @override
    async def _aremove_unhashed_id_from_kwargs(
        self, kwargs: dict[str, object]
    ) -> dict[str, object]:
        raw_discord_id: object | None = None

        field_name: str
        for field_name in ("discord_id", "member_id"):
            if not raw_discord_id:
                raw_discord_id = kwargs.pop(field_name, None)
            else:
                kwargs.pop(field_name, None)

        if not isinstance(raw_discord_id, int | str | None):
            raise TypeError

        discord_id: int | str | None = raw_discord_id

        if discord_id:
            kwargs["hashed_discord_id"] = self.model.hash_discord_id(discord_id)

        return kwargs


class RelatedDiscordMemberManager(BaseHashedIDManager["T_BaseDiscordMemberWrapper"]):
    """
    Manager class to create & retrieve instances of any concrete `BaseDiscordMemberWrapper`.

    This manager implements extra functionality to filter/create instances
    using a given discord_id that with be automatically hashed before saved to the database.
    """

    # noinspection SpellCheckingInspection
    @override
    def _remove_unhashed_id_from_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:
        raw_discord_id: object | None = None

        field_name: str
        for field_name in ("discord_id", "member_id"):
            if not raw_discord_id:
                raw_discord_id = kwargs.pop(field_name, None)
            else:
                kwargs.pop(field_name, None)

        if not isinstance(raw_discord_id, int | str | None):
            raise TypeError

        discord_id: int | str | None = raw_discord_id

        if discord_id:
            does_not_exist_error: ObjectDoesNotExist
            try:
                kwargs["discord_member"] = (
                    self.model.discord_member.field.remote_field.model.objects.get_or_create(  # type: ignore[attr-defined]
                        discord_id=discord_id,
                    )[0]
                )
            except (
                self.model.discord_member.field.remote_field.model.DoesNotExist
            ) as does_not_exist_error:  # type: ignore[attr-defined]
                raise self.model.DoesNotExist from does_not_exist_error

        return kwargs

    # noinspection SpellCheckingInspection
    @override
    async def _aremove_unhashed_id_from_kwargs(
        self, kwargs: dict[str, object]
    ) -> dict[str, object]:
        raw_discord_id: object | None = None

        field_name: str
        for field_name in ("discord_id", "member_id"):
            if not raw_discord_id:
                raw_discord_id = kwargs.pop(field_name, None)
            else:
                kwargs.pop(field_name, None)

        if not isinstance(raw_discord_id, int | str | None):
            raise TypeError

        discord_id: int | str | None = raw_discord_id

        if discord_id:
            does_not_exist_error: ObjectDoesNotExist
            try:
                kwargs["discord_member"] = (
                    await self.model.discord_member.field.remote_field.model.objects.aget_or_create(  # type: ignore[attr-defined] # noqa: E501
                        discord_id=discord_id,
                    )
                )[0]
            except (
                self.model.discord_member.field.remote_field.model.DoesNotExist
            ) as does_not_exist_error:  # type: ignore[attr-defined]
                raise self.model.DoesNotExist from does_not_exist_error

        return kwargs
