"""Manager classes used for DB access upon models."""

import abc
import logging
from typing import TYPE_CHECKING, final, override

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
    type Defaults = MutableMapping[str, object | Callable[[], object]] | None


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

