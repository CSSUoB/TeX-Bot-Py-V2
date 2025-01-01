"""Module for accessing society finances."""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Final

import aiohttp
import bs4
from bs4 import BeautifulSoup

from .core import (
    BASE_COOKIES,
    BASE_HEADERS,
    ORGANISATION_ADMIN_URL,
    ORGANISATION_ID,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger

__all__: "Sequence[str]" = ()

FINANCE_REDIRECT_URL: Final[str] = f"https://www.guildofstudents.com/sgf/{ORGANISATION_ID}/Landing/Member"
FINANCES_URL: Final[str] = f"https://guildofstudents.com/sgf/{ORGANISATION_ID}/Home/Dashboard/"
BASE_EXPENSE_URL: Final[str] = f"https://guildofstudents.com/sgf/{ORGANISATION_ID}/Request/Edit?RequestId="


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class TransactionType(Enum):
    """
    Enum for the different possible types of transactions.

    Attributes:
    ----------
    - Personal Expense: A personal expense
    - External Payment: A payment to an external entity
    - Purchase Order: A purchase order
    - Invoice: An invoice

    """

    PERSONAL_EXPENSE: str = "Personal Expense"
    EXTERNAL_PAYMENT: str = "External Payment"
    PURCHASE_ORDER: str = "Purchase Order"
    INVOICE: str = "Invoice"


async def get_account_balance() -> float | None:
    """Return the current account balance."""
    raise NotImplementedError  # NOTE: Not implemented because SGF does not currently support this but is due to be added imminently.


async def get_available_balance() -> float | None:
    """
    Return the current available balance.

    This is different from the account balance as it takes into account pending transactions.
    """
    cookie_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=BASE_COOKIES,
    )
    async with cookie_session, cookie_session.get(url=ORGANISATION_ADMIN_URL) as (
        cookie_response
    ):
        if cookie_response.status != 200:
            logger.debug("Returned a non 200 status code!!")
            logger.debug(cookie_response)
            return None

        cookies = cookie_response.cookies

    logger.debug(cookies)
    http_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=cookies,
    )
    async with http_session, http_session.get(url=FINANCE_REDIRECT_URL) as http_response:
        if http_response.status != 200:
            logger.debug("Returned a non 200 status code!!")
            logger.debug(http_response)
            return None

        response_html: str = await http_response.text()

    # check page title
    if "Login" in response_html:
        logger.debug("Not logged in!")
        return None

    available_balance_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
        markup=response_html,
        features="html.parser",
    ).find(
        name="div",
        attrs={"id": "accounts-summary"},
    )

    if available_balance_html is None or (
        isinstance(available_balance_html, bs4.NavigableString)
    ):
        logger.debug("Something went wrong!")
        logger.debug(response_html)
        return None

    logger.debug("Available balance HTML: %s", available_balance_html)

    return None

async def fetch_financial_transactions(limit: int | None = None, transaction_type: TransactionType | None = None) -> dict[str, str]:  # noqa: E501
    """
    Return the most recent `limit` transactions.

    If no limit is supplied, all transactions will be returned.
    Optional filter for type, if no type is supplied, all transactions will be returned.
    """
    raise NotImplementedError


async def fetch_transaction_from_id(transaction_id: int) -> dict[str, str]:
    """Return the transaction with the given ID."""
    """
    Transaction structure: {
        id: int,
        created by: str,
        linked_event_id: int | None,
        payee: str
        lines: {
            line 1 description: str,
            line 1 amount: float,
            line 2 description: str,
            line 2 amount: float,
            etc...
        }
        total_amount: float,
        status: str,
    }

    """
    EXPENSE_URL: Final[str] = BASE_EXPENSE_URL + str(transaction_id)

    http_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=BASE_COOKIES,
    )
    async with http_session, http_session.get(url=EXPENSE_URL) as http_response:
        if http_response.status != 200:
            logger.debug("Returned a non 200 status code!!")
            logger.debug(http_response)
            return {}

        response_html: str = await http_response.text()

    expense_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
        markup=response_html,
        features="html.parser",
    ).find(
        name="div",
        attrs={"class": "row container mx-auto"},
    )

    if expense_html is None or isinstance(expense_html, bs4.NavigableString):
        logger.debug("Something went wrong!")
        return {}

    raise NotImplementedError
