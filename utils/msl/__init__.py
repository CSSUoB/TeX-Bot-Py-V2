"""MSL utility classes & functions provided for use across the whole of the project."""

import certifi
import certifi
import ssl

from typing import TYPE_CHECKING

GLOBAL_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

from .memberships import get_full_membership_list, get_membership_count, is_student_id_member

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

__all__: "Sequence[str]" = (
    "get_full_membership_list",
    "get_membership_count",
    "is_student_id_member",
    "GLOBAL_SSL_CONTEXT",
)
