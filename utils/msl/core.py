"""Functions to enable interaction with MSL based SU websites."""

import datetime as dt
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Final

import aiohttp
from bs4 import BeautifulSoup

from config import settings

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import timezone
    from http.cookies import Morsel
    from logging import Logger

__all__: "Sequence[str]" = ()

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


DEFAULT_TIMEZONE: Final["timezone"] = dt.UTC
TODAYS_DATE: Final[datetime] = datetime.now(tz=DEFAULT_TIMEZONE)

CURRENT_YEAR_START_DATE: Final[datetime] = datetime(
    year=TODAYS_DATE.year if TODAYS_DATE.month >= 7 else TODAYS_DATE.year - 1,
    month=7,
    day=1,
    tzinfo=DEFAULT_TIMEZONE,
)

CURRENT_YEAR_END_DATE: Final[datetime] = datetime(
    year=TODAYS_DATE.year if TODAYS_DATE.month >= 7 else TODAYS_DATE.year - 1,
    month=6,
    day=30,
    tzinfo=DEFAULT_TIMEZONE,
)

BASE_HEADERS: Final["Mapping[str, str]"] = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

BASE_COOKIES: Final["Mapping[str, str]"] = {
    ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
}

ORGANISATION_ID: Final[str] = settings["MSL_ORGANISATION_ID"]

ORGANISATION_ADMIN_URL: Final[str] = f"https://www.guildofstudents.com/organisation/admin/{ORGANISATION_ID}/"


async def get_msl_context(url: str) -> tuple[dict[str, str], dict[str, str]]:
    """Get the required context headers, data and cookies to make a request to MSL."""
    http_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=BASE_COOKIES,
    )
    data_fields: dict[str, str] = {}
    cookies: dict[str ,str] = {}
    async with http_session, http_session.get(url=url) as field_data:
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
