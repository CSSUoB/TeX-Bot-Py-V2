"""Module for handling finance related MSL operations."""

import logging
from enum import Enum, auto
import re
from typing import TYPE_CHECKING, override

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
        self,
        expense_id: int,
        status: ExpenseStatus,
        expense_type: ExpenseType,
        payee: str,
        total_amount: float,
    ) -> None:
        self.id: int = expense_id
        self.status: ExpenseStatus = status
        self.type: ExpenseType = expense_type
        self.payee: str = payee  # NOTE: it's possible for a payee to be empty, but never None
        self.total_amount: float = total_amount

    @override
    def __repr__(self) -> str:
        return (
            f"Expense(id={self.id}, status={self.status.name}, type={self.type.name}, "
            f"payee='{self.payee}', total_amount={self.total_amount})"
        )


async def get_status_from_html(response_object: str) -> ExpenseStatus | None:
    """Extract the expense status from the HTML of an expense page."""
    status_match: re.Match[str] | None = re.search(r"StatusId:\s*(\d+)", response_object)
    if not status_match:
        return None

    expense_status: ExpenseStatus
    match status_match:
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
            return None

    return expense_status


async def get_type_from_html(response_html: bs4.BeautifulSoup) -> ExpenseType | None:
    """Extract the expense type from the HTML of an expense page."""
    page_title: bs4.Tag | bs4.NavigableString | None = response_html.find("title")
    if not isinstance(page_title, bs4.Tag) or not page_title.string:
        return None

    if "Edit Purchase Order" in page_title.string:
        return ExpenseType.PURCHASE_ORDER

    if "Edit Sales Invoice" in page_title.string:
        return ExpenseType.SALES_INVOICE

    if "Edit Expense Request" not in page_title.string:
        return None

    expense_type_html: bs4.Tag | bs4.NavigableString | None = response_html.find("select", {"id": "Fields_RequestSubtypeCode_"})
    if not isinstance(expense_type_html, bs4.Tag):
        return None

    expense_type_option_html = expense_type_html.find("option", selected=True)
    if not isinstance(expense_type_option_html, bs4.Tag):
        return None

    expense_type_option_value = str(expense_type_option_html.get("value", ""))

    if expense_type_option_value == "1":
        return ExpenseType.PERSONAL_EXPENSE

    if expense_type_option_value == "2":
        return ExpenseType.EXTERNAL_PAYMENT

    return None


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
    expense_status: ExpenseStatus | None = await get_status_from_html(response_object)
    if not expense_status:
        logger.warning(
            "Couldn't find the status of expense ID %d when scraping the expense page HTML.",
            expense_id,
        )
        logger.debug("Retrieved HTML: %s", response_object)
        return None


    response_html: bs4.BeautifulSoup = bs4.BeautifulSoup(response_object, "html.parser")

    expense_type: ExpenseType | None = await get_type_from_html(response_html)
    if not expense_type:
        logger.warning(
            "Couldn't find the type of expense ID %d when scraping the expense page HTML.",
            expense_id,
        )
        logger.debug("Retrieved HTML: %s", response_object)
        return None


    payee_name_html: bs4.Tag | bs4.NavigableString | None = response_html.find(
        "input", id="Fields_PayeeName_"
    )

    payee_name: str = ""
    if payee_name_html and isinstance(payee_name_html, bs4.Tag):
        payee_name = str(payee_name_html.get("value", ""))

    total_amount_html: bs4.Tag | bs4.NavigableString | None = response_html.find_all(
        "td", class_="amount"
    )[-1]

    if not isinstance(total_amount_html, bs4.Tag):
        logger.warning(
            "Couldn't find the total amount for expense ID %d when scraping the expense page HTML.",
            expense_id,
        )
        logger.debug("Retrieved HTML: %s", response_object)
        return None

    total_amount_text: str = total_amount_html.get_text(strip=True).replace(",", "")
    total_amount: float | None
    try:
        total_amount = float(total_amount_text)
    except ValueError:
        logger.warning(
            "Couldn't parse the total amount for expense ID %d when scraping the expense page HTML. Found text: %s",
            expense_id,
            total_amount_text,
        )
        return None

    return Expense(
        expense_id=expense_id,
        status=expense_status,
        expense_type=expense_type,
        payee=payee_name,
        total_amount=total_amount,
    )
