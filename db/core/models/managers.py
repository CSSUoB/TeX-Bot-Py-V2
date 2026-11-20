"""Model classes that store extra information between individual event handling call-backs."""

__all__: Sequence[str] = ()


lazy from collections.abc import Sequence

from django.db.models import Manager
lazy from django.db.models import Model

lazy from . import DiscordMember  # noqa: F401


class HashedDiscordMemberManager(Manager["DiscordMember"]):
    pass


class RelatedDiscordMemberManager[T_Model: "Model"](Manager[T_Model]):
    pass
