"""Module for checking membership status."""

from collections.abc import Sequence

__all__: Sequence[str] = ("get_full_membership_list", "is_student_id_member")

import logging
from logging import Logger
from typing import Final

import aiohttp
import bs4
from bs4 import BeautifulSoup

from .core import BASE_COOKIES, BASE_HEADERS, ORGANISATION_ID

MEMBERS_LIST_URL: Final[str] = f"https://guildofstudents.com/organisation/memberlist/{ORGANISATION_ID}/?sort=groups"

logger: Final[Logger] = logging.getLogger("TeX-Bot")


async def get_full_membership_list() -> set[tuple[str, int]]:
    """Get a list of tuples of student ID to names."""
    http_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=BASE_COOKIES,
    )
    async with http_session, http_session.get(url=MEMBERS_LIST_URL) as http_response:
        response_html: str = await http_response.text()

    standard_members_table: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
        markup=response_html,
        features="html.parser",
    ).find(
        name="table",
        attrs={"id": "ctl00_Main_rptGroups_ctl03_gvMemberships"},
    )

    all_members_table: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
        markup=response_html,
        features="html.parser",
    ).find(
        name="table",
        attrs={"id": "ctl00_Main_rptGroups_ctl05_gvMemberships"},
    )

    if standard_members_table is None or all_members_table is None:
        logger.warning("One or both of the membership tables could not be found!")
        logger.debug(response_html)
        return set()

    if (
        isinstance(standard_members_table, bs4.NavigableString) or
        isinstance(all_members_table, bs4.NavigableString)
    ):
        logger.warning(
            "Both membership tables were found but one or both are the wrong format!",
        )
        logger.debug(standard_members_table)
        logger.debug(all_members_table)
        return set()

    standard_members: list[bs4.Tag] = standard_members_table.find_all(name="tr")
    all_members: list[bs4.Tag] = all_members_table.find_all(name="tr")

    standard_members.pop(0)
    all_members.pop(0)

    member_list: set[tuple[str, int]] = {(
        member.find_all(name="td")[0].text.strip(),
        member.find_all(name="td")[1].text.strip(),  # NOTE: This will not properly handle external members who do not have an ID... There does not appear to be a solution to this other than simply checking manually.
        )
        for member in standard_members + all_members
    }

    return member_list


async def is_student_id_member(student_id: str | int) -> bool:
    """Check if the student ID is a member of the society."""
    # TODO: Implement cache so that a query is only made to the website if the student ID being checked is not in the cache
    all_ids: set[str] = {
        str(member[1]) for member in await get_full_membership_list()
    }

    return str(student_id) in all_ids


async def get_membership_count() -> int:
    """Return the total number of members."""
    return len(await get_full_membership_list())
