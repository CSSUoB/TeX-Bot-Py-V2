"""Manager classes used for DB access upon models."""

import logging
from typing import TYPE_CHECKING, override

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Manager

__all__ = ("RelatedDiscordMemberManager",)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class RelatedDiscordMemberManager(Manager):
    """
    Manager class to create and retrieve instances of any concrete `BaseDiscordMemberWrapper`.

    This manager implements extra functionality to filter/create instances
    using a given discord_id that will be used directly.
    """

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
                self.model.discord_member.field.remote_field.model.DoesNotExist  # type: ignore[attr-defined]
            ) as does_not_exist_error:
                raise self.model.DoesNotExist from does_not_exist_error

        return kwargs

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
                self.model.discord_member.field.remote_field.model.DoesNotExist  # type: ignore[attr-defined]
            ) as does_not_exist_error:
                raise self.model.DoesNotExist from does_not_exist_error

        return kwargs
