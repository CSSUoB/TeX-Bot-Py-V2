"""Module for checking membership status."""

import contextlib
import logging
from typing import TYPE_CHECKING

import aiohttp
import bs4
from bs4 import BeautifulSoup

from config import settings
from utils import GLOBAL_SSL_CONTEXT

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from http.cookies import Morsel
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


async def fetch_msl_context(url: str) -> tuple[dict[str, str], dict[str, str]]:
    """Get the required context headers, data and cookies to make a request to MSL."""
    http_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_SU_PLATFORM_WEB_HEADERS,
        cookies=BASE_SU_PLATFORM_WEB_COOKIES,
    )
    data_fields: dict[str, str] = {}
    cookies: dict[str, str] = {}
    async with http_session, http_session.get(url=url, ssl=GLOBAL_SSL_CONTEXT) as field_data:
        data_response = BeautifulSoup(
            markup=await field_data.text(),
            features="html.parser",
        )

        for field in data_response.find_all(name="input"):
            if field.get("name") and field.get("value"):
                data_fields[field.get("name")] = field.get("value")

        for cookie in field_data.cookies:
            cookie_morsel: Morsel[str] | None = field_data.cookies.get(cookie)
            if cookie_morsel is not None:
                cookies[cookie] = cookie_morsel.value
        cookies[".ASPXAUTH"] = settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"]

    return data_fields, cookies


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

    standard_members_table: bs4.Tag | bs4.NavigableString | None = parsed_html.find(
        name="table",
        attrs={"id": "ctl00_ctl00_Main_AdminPageContent_rptGroups_ctl03_gvMemberships"},
    )

    all_members_table: bs4.Tag | bs4.NavigableString | None = parsed_html.find(
        name="table",
        attrs={"id": "ctl00_ctl00_Main_AdminPageContent_rptGroups_ctl05_gvMemberships"},
    )

    if standard_members_table is None or all_members_table is None:
        logger.warning("One or both of the membership tables could not be found!")
        logger.debug(response_html)
        return set()

    if isinstance(standard_members_table, bs4.NavigableString) or isinstance(
        all_members_table, bs4.NavigableString
    ):
        logger.warning(
            "Both membership tables were found but one or both are the wrong format!",
        )
        logger.debug(standard_members_table)
        logger.debug(all_members_table)
        return set()

    with contextlib.suppress(IndexError):
        all_rows: list[bs4.Tag] = (
            standard_members_table.find_all(name="tr")[1:]
            + all_members_table.find_all(name="tr")[1:]
        )

    for member in all_rows:
        with contextlib.suppress(ValueError):
            _membership_list_cache.add(int(member.find_all(name="td")[1].text.strip()))

    return _membership_list_cache


async def is_id_a_community_group_member(student_id: int) -> bool:
    """Check if the given ID is a member of your community group."""
    if student_id in _membership_list_cache:
        return True

    logger.debug(
        "ID %s not found in community group membership list cache; Fetching updated list.",
        student_id,
    )

    return student_id in await fetch_community_group_members_list()

async def fetch_community_group_members_count() -> int:
    """Return the total number of members in your community group."""
    return len(await fetch_community_group_members_list())
