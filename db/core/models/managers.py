"""Model classes that store extra information between individual event handling call-backs."""

from typing import TYPE_CHECKING

from django.db.models import Manager

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = ()


class RelatedDiscordMemberManager(Manager):
    pass


class HashedDiscordMemberManager(Manager):
    pass
