"""Functions to enable interaction with MSL based SU websites."""

from collections.abc import Sequence

__all__: Sequence[str] = ("MSL",)


import logging
from collections.abc import Mapping
from logging import Logger
from typing import TYPE_CHECKING, Final

import aiohttp
import bs4
from bs4 import BeautifulSoup

from config import settings

if TYPE_CHECKING:
    from http.cookies import Morsel


logger: Final[Logger] = logging.getLogger("TeX-Bot")


MSL_URLS: Final[Mapping[str, str]] = {
    "EVENT_LIST": "https://www.guildofstudents.com/events/edit/6531/",
    "MEMBERS_LIST": settings["MEMBERS_LIST_URL"],
}

BASE_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

BASE_COOKIES: Final[Mapping[str, str]] = {
    ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
}

FROM_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtFromDate"
TO_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtToDate"
BUTTON_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$fsSetDates$btnSubmit"
EVENT_TABLE_ID: Final[str] = "ctl00_ctl00_Main_AdminPageContent_gvEvents"

class MSL:
    """Class to define the functions related to MSL based SU websites."""

    async def _get_msl_context(self, url: str) -> tuple[dict[str, str], dict[str, str]]:
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

    class MSLEvents:
        """Class to define Event specific MSL methods."""

        async def _get_all_guild_events(self, from_date: str, to_date: str) -> dict[str, str]:
            """Fetch all events on the guild website."""
            EVENT_LIST_URL: Final[str] = MSL_URLS["EVENT_LIST"]

            data_fields, cookies = await MSL._get_msl_context(self, url=EVENT_LIST_URL)

            form_data: dict[str, str] = {
                FROM_DATE_KEY: from_date,
                TO_DATE_KEY: to_date,
                BUTTON_KEY: "Find Events",
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATEENCRYPTED": "",
            }

            data_fields.update(form_data)

            session_v2: aiohttp.ClientSession = aiohttp.ClientSession(
                headers=BASE_HEADERS,
                cookies=cookies,
            )
            async with session_v2, session_v2.post(url=EVENT_LIST_URL, data=data_fields) as http_response:  # noqa: E501
                if http_response.status != 200:
                    logger.debug("Returned a non 200 status code!!")
                    logger.debug(http_response)
                    return {}

                response_html: str = await http_response.text()

            event_table_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
                    markup=response_html,
                    features="html.parser",
                ).find(
                    name="table",
                    attrs={"id": EVENT_TABLE_ID},
                )

            if event_table_html is None or isinstance(event_table_html, bs4.NavigableString):
                # TODO: something went wrong!!
                logger.debug("Something went wrong!")
                return {}

            if "There are no events" in str(event_table_html):
                # TODO: No events!!
                logger.debug("No events were found!")
                return {}

            event_list: list[bs4.Tag] = event_table_html.find_all(name="tr")

            event_list.pop(0)

            event_ids: dict[str, str] = {
                event.find(name="a").get("href").split("/")[5]: event.find(name="a").text  # type: ignore[union-attr]
                for event in event_list
            }

            return event_ids


    class MSLMemberships:
        """Class to define Membership specific MSL methods."""


    class MSLSalesReports:
        """Class to define Sales Reports specific MSL methods."""

