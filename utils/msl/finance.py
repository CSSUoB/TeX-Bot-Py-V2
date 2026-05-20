"""Module for handling finance related MSL operations."""

import logging
from enum import Enum, auto
from typing import TYPE_CHECKING

from .authorisation import SUPlatformAccessCookieStatus, get_su_platform_access_cookie_status
from .core import SGF_URL, su_platform_client

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final, Optional


__all__: "Sequence[str]" = ()


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class ExpenseStatus(Enum):
    """Enum class defining the status of an MSL expense."""

    DRAFT = 2
    PENDING_COMMITTEE_APPROVAL = 3
    PENDING_L2_APPROVAL = 4
    PENDING_L3_APPROVAL = 5
    REFERRED = 32
    REJECTED = 33

    PENDING_FINANCE_APPROVAL = auto()
    PENDING_FINANCE_PROCESSING = auto()
    PENDING_PAYMENT = 10
    PAID = 30

    PO_OR_INVOICE_APPROVED = 40


class ExpenseType(Enum):
    """Enum class defining the type of an MSL expense."""

    PERSONAL_EXPENSE = auto()
    EXTERNAL_PAYMENT = auto()
    PURCHASE_ORDER = auto()
    SALES_INVOICE = auto()


class Expense:
    """Class representing an MSL expense."""

    def __init__(
        self, expense_id: int, status: ExpenseStatus, expense_type: ExpenseType
    ) -> None:
        self.id = expense_id
        self.status = status
        self.type = expense_type


async def get_expense(expense_id: int) -> "Expense | None":
    """Retrieve the details of an MSL expense."""
    EXPENSE_URL: "Final[str]" = f"{SGF_URL}Request/Edit?RequestId={expense_id}"

    status: SUPlatformAccessCookieStatus = await get_su_platform_access_cookie_status()

    if status != SUPlatformAccessCookieStatus.AUTHORISED:
        logger.info(
            "Failed to retrieve expense details for expense ID %d. No admin access.",
            expense_id,
        )
        return None

    response_object: str = await su_platform_client.fetch_url_content(EXPENSE_URL)

    if "<!-- StatusId:" not in response_object:
        logger.info(
            "Expense ID %d could not be found.",
            expense_id,
        )



    return None
