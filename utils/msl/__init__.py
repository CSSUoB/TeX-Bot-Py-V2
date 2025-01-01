"""MSL utility classes & functions provided for use across the whole of the project."""

from typing import TYPE_CHECKING

from .events import create_event, get_all_guild_events
from .finances import (
    fetch_financial_transactions,
    fetch_transaction_from_id,
    get_account_balance,
)
from .memberships import get_full_membership_list, is_student_id_member
from .reports import (
    get_product_customisations,
    get_product_sales,
    update_current_year_sales_report,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "create_event",
    "fetch_financial_transactions",
    "fetch_transaction_from_id",
    "get_account_balance",
    "get_all_guild_events",
    "get_full_membership_list",
    "get_product_customisations",
    "get_product_sales",
    "is_student_id_member",
    "update_current_year_sales_report",
)
