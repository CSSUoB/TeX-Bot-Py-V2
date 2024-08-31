"""Module for accessing society finances."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import logging
from enum import Enum
from logging import Logger
from typing import Final

from .core import ORGANISATION_ID

FINANCES_URL: Final[str] = f"https://guildofstudents.com/sgf/{ORGANISATION_ID}/Home/Dashboard/"


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


async def fetch_transaction_from_id(transaction_id: int) -> dict[str, str]:  # noqa: ARG001
    """Return the transaction with the given ID."""
    return {}




