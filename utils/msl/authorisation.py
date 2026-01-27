"""Module for authorisation checks."""

import logging
from typing import TYPE_CHECKING

import aiohttp
import bs4

from cogs.check_su_platform_authorisation import SUPlatformAccessCookieStatus
from config import settings
from utils import GLOBAL_SSL_CONTEXT

from .core import BASE_COOKIES, BASE_HEADERS

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = (
    "get_su_platform_access_cookie_status",
    "get_su_platform_organisations",
)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


SU_PLATFORM_PROFILE_URL: "Final[str]" = "https://guildofstudents.com/profile"
SU_PLATFORM_ORGANISATION_URL: "Final[str]" = (
    "https://www.guildofstudents.com/organisation/admin"
)


async def _fetch_url_content_with_session(url: str) -> str:
    """Fetch the HTTP content at the given URL, using a shared aiohttp session."""
    async with (
        aiohttp.ClientSession(headers=BASE_HEADERS, cookies=BASE_COOKIES) as http_session,
        http_session.get(url=url, ssl=GLOBAL_SSL_CONTEXT) as http_response,
    ):
        return await http_response.text()


async def get_su_platform_access_cookie_status() -> SUPlatformAccessCookieStatus:
    """Retrieve the current validity status of the SU platform access cookie."""
    response_object: bs4.BeautifulSoup = bs4.BeautifulSoup(
        await _fetch_url_content_with_session(SU_PLATFORM_PROFILE_URL), "html.parser"
    )
    page_title: bs4.Tag | bs4.NavigableString | None = response_object.find("title")
    if not page_title or "Login" in str(page_title):
        logger.debug("Token is invalid or expired.")
        return SUPlatformAccessCookieStatus.INVALID

    organisation_admin_url: str = (
        f"{SU_PLATFORM_ORGANISATION_URL}/{settings['ORGANISATION_ID']}"
    )
    response_html: str = await _fetch_url_content_with_session(organisation_admin_url)

    if "admin tools" in response_html.lower():
        return SUPlatformAccessCookieStatus.AUTHORISED

    if "You do not have any permissions for this organisation" in response_html.lower():
        return SUPlatformAccessCookieStatus.VALID

    logger.warning(
        "Unexpected response when checking SU platform access cookie authorisation."
    )
    return SUPlatformAccessCookieStatus.INVALID


async def get_su_platform_organisations() -> "Iterable[str]":
    """Retrieve the MSL organisations the current SU platform cookie has access to."""
    response_object: bs4.BeautifulSoup = bs4.BeautifulSoup(
        await _fetch_url_content_with_session(SU_PLATFORM_PROFILE_URL), "html.parser"
    )

    page_title: bs4.Tag | bs4.NavigableString | None = response_object.find("title")

    if not page_title:
        logger.warning(
            "Profile page returned no content when checking "
            "SU platform access cookie's authorisation."
        )
        return ()

    if "Login" in str(page_title):
        logger.warning(
            "Authentication redirected to login page. "
            "SU platform access cookie is invalid or expired."
        )
        return ()

    profile_section_html: bs4.Tag | bs4.NavigableString | None = response_object.find(
        "div", {"id": "profile_main"}
    )

    if profile_section_html is None:
        logger.warning(
            "Couldn't find the profile section of the user "
            "when scraping the SU platform's website HTML."
        )
        logger.debug("Retrieved HTML: %s", response_object.text)
        return ()

    user_name: bs4.Tag | bs4.NavigableString | int | None = profile_section_html.find("h1")

    if not isinstance(user_name, bs4.Tag):
        logger.warning("Found user profile on the SU platform but couldn't find their name.")
        logger.debug("Retrieved HTML: %s", response_object.text)
        return ()

    parsed_html: bs4.Tag | bs4.NavigableString | None = response_object.find(
        "ul", {"id": "ulOrgs"}
    )

    if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
        NO_ADMIN_TABLE_MESSAGE: Final[str] = (
            f"Failed to retrieve the admin table for user: {user_name.string}. "
            "Please check you have used the correct SU platform access token!"
        )
        logger.warning(NO_ADMIN_TABLE_MESSAGE)
        return ()

    organisations: Iterable[str] = [
        list_item.get_text(strip=True) for list_item in parsed_html.find_all("li")
    ]

    logger.debug(
        "SU platform access cookie has admin authorisation to: %s as user %s",
        organisations,
        user_name.text,
    )

    return organisations
