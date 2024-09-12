"""Module for accessing society finances."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import logging
from enum import Enum
from logging import Logger
from typing import Final

import aiohttp
import bs4
from bs4 import BeautifulSoup

from .core import BASE_COOKIES, BASE_HEADERS, ORGANISATION_ID

FINANCES_URL: Final[str] = f"https://guildofstudents.com/sgf/{ORGANISATION_ID}/Home/Dashboard/"
BASE_EXPENSE_URL: Final[str] = f"https://guildofstudents.com/sgf/{ORGANISATION_ID}/Request/Edit?RequestId="


logger: Final[Logger] = logging.getLogger("TeX-Bot")


class TransactionType(Enum):
    """
    Enum for the different possible types of transactions.

    Attributes
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
    raise NotImplementedError  # NOTE: Not implemented because SGF does not currently support this but is due to be added imminently.


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
