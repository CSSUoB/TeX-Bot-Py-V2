"""MSL utility classes & functions provided for use across the whole of the project."""

from typing import TYPE_CHECKING

from .authorisation import get_su_platform_access_cookie_status, get_su_platform_organisations
from .memberships import (
    fetch_community_group_members_count,
    fetch_community_group_members_list,
    is_id_a_community_group_member,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "GLOBAL_SSL_CONTEXT",
    "fetch_community_group_members_count",
    "fetch_community_group_members_list",
    "get_su_platform_access_cookie_status",
    "get_su_platform_organisations",
    "is_id_a_community_group_member",
)
