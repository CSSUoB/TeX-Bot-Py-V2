"""MSL utility classes & functions provided for use across the whole of the project."""

import ssl
from typing import TYPE_CHECKING

import certifi

GLOBAL_SSL_CONTEXT: ssl.SSLContext = ssl.create_default_context(cafile=certifi.where())

from .memberships import get_full_membership_list, get_membership_count, is_student_id_member

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "GLOBAL_SSL_CONTEXT",
    "get_full_membership_list",
    "get_membership_count",
    "is_student_id_member",
)
