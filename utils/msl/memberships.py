"""Module for checking membership status."""

import contextlib
import logging
from typing import TYPE_CHECKING

import aiohttp
import bs4
from bs4 import BeautifulSoup

from config import settings
from exceptions import MSLMembershipError
from utils import GLOBAL_SSL_CONTEXT

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = (
    "fetch_community_group_members_count",
    "fetch_community_group_members_list",
    "is_id_a_community_group_member",
)


BASE_SU_PLATFORM_WEB_HEADERS: "Final[Mapping[str, str]]" = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

BASE_SU_PLATFORM_WEB_COOKIES: "Final[Mapping[str, str]]" = {
    ".ASPXAUTH": settings["SU_PLATFORM_ACCESS_COOKIE"],
}

MEMBERS_LIST_URL: "Final[str]" = f"https://guildofstudents.com/organisation/memberlist/{settings['ORGANISATION_ID']}/?sort=groups"

_membership_list_cache: set[int] = set()


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


async def fetch_community_group_members_list() -> set[int]:
    """
    Make a web request to fetch your community group's full membership list.

    Returns a set of IDs.
    """
    async with (
        aiohttp.ClientSession(
            headers=BASE_SU_PLATFORM_WEB_HEADERS, cookies=BASE_SU_PLATFORM_WEB_COOKIES
        ) as http_session,
        http_session.get(url=MEMBERS_LIST_URL, ssl=GLOBAL_SSL_CONTEXT) as http_response,
    ):
        response_html: str = await http_response.text()

    parsed_html: BeautifulSoup = BeautifulSoup(markup=response_html, features="html.parser")

    member_ids: set[int] = set()

    table_id: str
    for table_id in (
        "ctl00_ctl00_Main_AdminPageContent_rptGroups_ctl03_gvMemberships",
        "ctl00_ctl00_Main_AdminPageContent_rptGroups_ctl05_gvMemberships",
    ):
        filtered_table: bs4.Tag | bs4.NavigableString | None = parsed_html.find(
            name="table", attrs={"id": table_id}
        )

        if filtered_table is None:
            logger.warning("Membership table with ID %s could not be found.", table_id)
            logger.debug(response_html)
            continue

        if isinstance(filtered_table, bs4.NavigableString):
            INVALID_MEMBER_TABLE_FORMAT_MESSAGE: str = (
                f"Membership table with ID {table_id} was found but is in the wrong format."
            )
            logger.warning(INVALID_MEMBER_TABLE_FORMAT_MESSAGE)
            logger.debug(filtered_table)
            raise MSLMembershipError(message=INVALID_MEMBER_TABLE_FORMAT_MESSAGE)

        with contextlib.suppress(IndexError):
            rows: list[bs4.Tag] = filtered_table.find_all(name="tr")[1:]
            for member in rows:
                raw_id: str = member.find_all(name="td")[1].text.strip()
                try:
                    member_ids.add(int(raw_id))
                except ValueError:
                    logger.warning(
                        "Failed to convert ID '%s' in membership table to an integer", raw_id
                    )

    if not member_ids:  # NOTE: this should never be possible, because to fetch the page you need to have admin access, which requires being a member.
        NO_MEMBERS_MESSAGE: Final[str] = "No members were found in either membership table."
        logger.warning(NO_MEMBERS_MESSAGE)
        logger.debug(response_html)
        raise MSLMembershipError(message=NO_MEMBERS_MESSAGE)

    _membership_list_cache.clear()
    _membership_list_cache.update(member_ids)

    return _membership_list_cache


async def is_id_a_community_group_member(member_id: int) -> bool:
    """Check if the given ID is a member of your community group."""
    if member_id in _membership_list_cache:
        return True

    logger.debug(
        "ID %s not found in community group membership list cache; Fetching updated list.",
        member_id,
    )

    return member_id in await fetch_community_group_members_list()


async def fetch_community_group_members_count() -> int:
    """Return the total number of members in your community group."""
    return len(await fetch_community_group_members_list())
