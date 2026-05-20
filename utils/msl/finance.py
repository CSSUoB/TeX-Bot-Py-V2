"""Module for handling finance related MSL operations."""

import logging
from enum import Enum, auto
import re
from typing import TYPE_CHECKING

import bs4

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
    CANCELLED = 31

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

    type_match: re.Match[str] | None = re.search(r"StatusId:\s*(\d+)", response_object)
    if not type_match:
        logger.info(
            "Expense ID %d could not be found.",
            expense_id,
        )
        return None

    expense_status: ExpenseStatus
    match type_match:
        case re.Match() as m if m.group(1) == "2":
            expense_status = ExpenseStatus.DRAFT
        case re.Match() as m if m.group(1) == "3":
            expense_status = ExpenseStatus.PENDING_COMMITTEE_APPROVAL
        case re.Match() as m if m.group(1) == "4":
            expense_status = ExpenseStatus.PENDING_L2_APPROVAL
        case re.Match() as m if m.group(1) == "5":
            expense_status = ExpenseStatus.PENDING_L3_APPROVAL
        case re.Match() as m if m.group(1) == "32":
            expense_status = ExpenseStatus.REFERRED
        case re.Match() as m if m.group(1) == "33":
            expense_status = ExpenseStatus.REJECTED
        case re.Match() as m if m.group(1) == "10":
            expense_status = ExpenseStatus.PENDING_PAYMENT
        case re.Match() as m if m.group(1) == "30":
            expense_status = ExpenseStatus.PAID
        case re.Match() as m if m.group(1) == "31":
            expense_status = ExpenseStatus.CANCELLED
        case re.Match() as m if m.group(1) == "40":
            expense_status = ExpenseStatus.PO_OR_INVOICE_APPROVED
        case _:
            logger.warning(
                "Expense ID %d has an unrecognised status code: %s",
                expense_id,
                type_match.group(1),
            )
            return None

    logger.debug("Expense ID %d has status: %s", expense_id, expense_status.name)


    expense_type_html = bs4.BeautifulSoup(response_object, "html.parser").find(
        "select", {"id": "Fields_RequestSubtypeCode_"}
    )

    if not isinstance(expense_type_html, bs4.Tag):
        logger.debug("Expense is not a specific type...")
        return None

    expense_type_option_html = expense_type_html.find_all("option", selected=True)

    expense_type: Optional[ExpenseType] = None


    logger.debug(expense_type_option_html)



    return None
