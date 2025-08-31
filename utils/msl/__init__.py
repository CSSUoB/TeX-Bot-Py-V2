"""MSL utility classes & functions provided for use across the whole of the project."""

from typing import TYPE_CHECKING

from .memberships import get_full_membership_list, get_membership_count, is_student_id_member

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "GLOBAL_SSL_CONTEXT",
    "get_full_membership_list",
    "get_membership_count",
    "is_student_id_member",
)
