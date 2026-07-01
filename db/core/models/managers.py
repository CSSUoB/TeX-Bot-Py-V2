"""Model classes that store extra information between individual event handling call-backs."""

from typing import TYPE_CHECKING

from django.db.models import Manager

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.db.models import Model

    from . import DiscordMember  # noqa: F401

__all__: Sequence[str] = ()


class HashedDiscordMemberManager(Manager["DiscordMember"]):
    pass


class RelatedDiscordMemberManager[T_Model: "Model"](Manager[T_Model]):
    pass
