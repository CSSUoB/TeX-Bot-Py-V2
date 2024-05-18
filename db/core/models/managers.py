"""Manager classes used for DB access upon models."""

from collections.abc import Sequence

__all__: Sequence[str] = ("HashedDiscordMemberManager", "RelatedDiscordMemberManager")


import abc
from collections.abc import Callable, MutableMapping
from typing import TYPE_CHECKING, TypeAlias, TypeVar, override

from django.db.models import Manager, QuerySet

if TYPE_CHECKING:
    from django.core.exceptions import ObjectDoesNotExist

    # noinspection PyUnresolvedReferences
    from .utils import AsyncBaseModel

    T_model = TypeVar("T_model", bound=AsyncBaseModel)

Defaults: TypeAlias = (
    MutableMapping[str, object | Callable[[], object]]
    | None
)


class BaseHashedIDManager(Manager["T_model"], abc.ABC):
    """Base manager class to remove a given unhashed ID before executing a query."""

    use_in_migrations: bool = True

    # noinspection SpellCheckingInspection
    @abc.abstractmethod
    def _remove_unhashed_id_from_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:
        """Remove any unhashed ID values from the kwargs dict before executing a query."""

    # noinspection SpellCheckingInspection
    @abc.abstractmethod
    async def _aremove_unhashed_id_from_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:  # noqa: E501
        """Remove any unhashed_id values from the kwargs dict before executing a query."""

    @override
    def get(self, *args: object, **kwargs: object) -> "T_model":
        return super().get(*args, **self._remove_unhashed_id_from_kwargs(kwargs))

    @override
    async def aget(self, *args: object, **kwargs: object) -> "T_model":
        return await super().aget(
            *args,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def filter(self, *args: object, **kwargs: object) -> QuerySet["T_model"]:
        return super().filter(*args, **self._remove_unhashed_id_from_kwargs(kwargs))

    @override
    def exclude(self, *args: object, **kwargs: object) -> QuerySet["T_model"]:
        return super().exclude(*args, **self._remove_unhashed_id_from_kwargs(kwargs))

    @override
    def create(self, **kwargs: object) -> "T_model":
        return super().create(**self._remove_unhashed_id_from_kwargs(kwargs))

    # noinspection SpellCheckingInspection
    @override
    async def acreate(self, **kwargs: object) -> "T_model":
        return await super().acreate(**(await self._aremove_unhashed_id_from_kwargs(kwargs)))

    @override
    def get_or_create(self, defaults: Defaults = None, **kwargs: object) -> tuple["T_model", bool]:  # noqa: E501
        return super().get_or_create(
            defaults=defaults,
            **self._remove_unhashed_id_from_kwargs(kwargs),
        )

    @override
    async def aget_or_create(self, defaults: Defaults = None, **kwargs: object) -> tuple["T_model", bool]:  # noqa: E501
        return await super().aget_or_create(
            defaults=defaults,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def update_or_create(self, defaults: Defaults = None, create_defaults: Defaults = None, **kwargs: object) -> tuple["T_model", bool]:  # noqa: E501
        return super().get_or_create(
            defaults=defaults,
            create_defaults=create_defaults,
            **self._remove_unhashed_id_from_kwargs(kwargs),
        )

    # noinspection SpellCheckingInspection
    @override
    async def aupdate_or_create(self, defaults: Defaults = None, create_defaults: Defaults = None, **kwargs: object) -> tuple["T_model", bool]:  # noqa: E501
        return await super().aupdate_or_create(
            defaults=defaults,
            create_defaults=create_defaults,
            **(await self._aremove_unhashed_id_from_kwargs(kwargs)),
        )

    @override
    def update(self, **kwargs: object) -> int:
        return super().update(**self._remove_unhashed_id_from_kwargs(kwargs))

    # noinspection SpellCheckingInspection
    @override
    async def aupdate(self, **kwargs: object) -> int:
        return await super().aupdate(**(await self._aremove_unhashed_id_from_kwargs(kwargs)))


class HashedDiscordMemberManager(BaseHashedIDManager["DiscordMember"]):
    """
    Manager class to create & retrieve DiscordMember model instances.

    This manager implements extra functionality to filter/create instances
    using a given discord_id that with be automatically hashed, before saved to the database.
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

        discord_id: int | str | None = raw_discord_id  # type: ignore[assignment]

        if discord_id:
            kwargs["hashed_discord_id"] = self.model.hash_discord_id(discord_id)

        return kwargs

    # noinspection SpellCheckingInspection
    @override
    async def _aremove_unhashed_id_from_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:  # noqa: E501
        raw_discord_id: object | None = None

        field_name: str
        for field_name in ("discord_id", "member_id"):
            if not raw_discord_id:
                raw_discord_id = kwargs.pop(field_name, None)
            else:
                kwargs.pop(field_name, None)

        if not isinstance(raw_discord_id, int | str | None):
            raise TypeError

        discord_id: int | str | None = raw_discord_id  # type: ignore[assignment]

        if discord_id:
            kwargs["hashed_discord_id"] = self.model.hash_discord_id(discord_id)

        return kwargs


class RelatedDiscordMemberManager(BaseHashedIDManager["BaseDiscordMemberWrapper"]):
    """
    Manager class to create & retrieve instances of any concrete `BaseDiscordMemberWrapper`.

    This manager implements extra functionality to filter/create instances
    using a given discord_id that with be automatically hashed, before saved to the database.
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

        discord_id: int | str | None = raw_discord_id  # type: ignore[assignment]

        if discord_id:
            does_not_exist_error: ObjectDoesNotExist
            try:
                kwargs["discord_member"] = (
                    self.model.discord_member.field.remote_field.model.objects.get_or_create(  # type: ignore[attr-defined]
                        discord_id=discord_id,
                    )[0]
                )
            except self.model.discord_member.field.remote_field.model.DoesNotExist as does_not_exist_error:  # type: ignore[attr-defined] # noqa: E501
                raise self.model.DoesNotExist from does_not_exist_error

        return kwargs

    # noinspection SpellCheckingInspection
    @override
    async def _aremove_unhashed_id_from_kwargs(self, kwargs: dict[str, object]) -> dict[str, object]:  # noqa: E501
        raw_discord_id: object | None = None

        field_name: str
        for field_name in ("discord_id", "member_id"):
            if not raw_discord_id:
                raw_discord_id = kwargs.pop(field_name, None)
            else:
                kwargs.pop(field_name, None)

        if not isinstance(raw_discord_id, int | str | None):
            raise TypeError

        discord_id: int | str | None = raw_discord_id  # type: ignore[assignment]

        if discord_id:
            does_not_exist_error: ObjectDoesNotExist
            try:
                kwargs["discord_member"] = (
                    await self.model.discord_member.field.remote_field.model.objects.aget_or_create(  # type: ignore[attr-defined] # noqa: E501
                        discord_id=discord_id,
                    )
                )[0]
            except self.model.discord_member.field.remote_field.model.DoesNotExist as does_not_exist_error:  # type: ignore[attr-defined] # noqa: E501
                raise self.model.DoesNotExist from does_not_exist_error

        return kwargs
