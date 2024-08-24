"""Module for fetching events from the guild website."""

from collections.abc import Sequence

__all__: Sequence[str] = ("get_all_guild_events", "create_event")

import logging
from logging import Logger
from typing import Final

import aiohttp
import bs4
from bs4 import BeautifulSoup

from .core import BASE_HEADERS, ORGANISATION_ID, get_msl_context

EVENTS_FROM_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtFromDate"
EVENTS_TO_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtToDate"
EVENTS_BUTTON_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$fsSetDates$btnSubmit"
EVENTS_TABLE_ID: Final[str] = "ctl00_ctl00_Main_AdminPageContent_gvEvents"
CREATE_EVENT_URL: Final[str] = f"https://www.guildofstudents.com/events/edit/event/{ORGANISATION_ID}/"
EVENT_LIST_URL: Final[str] = f"https://www.guildofstudents.com/events/edit/{ORGANISATION_ID}/"


logger: Final[Logger] = logging.getLogger("TeX-Bot")


async def get_all_guild_events(from_date: str, to_date: str) -> dict[str, str]:
    """Fetch all events on the guild website."""
    data_fields, cookies = await get_msl_context(url=EVENT_LIST_URL)

    form_data: dict[str, str] = {
        EVENTS_FROM_DATE_KEY: from_date,
        EVENTS_TO_DATE_KEY: to_date,
        EVENTS_BUTTON_KEY: "Find Events",
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
            attrs={"id": EVENTS_TABLE_ID},
        )

    if event_table_html is None or isinstance(event_table_html, bs4.NavigableString):
        logger.debug("Something went wrong!")
        return {}

    if "There are no events" in str(event_table_html):
        logger.debug("No events were found!")
        return {}

    event_list: list[bs4.Tag] = event_table_html.find_all(name="tr")

    event_list.pop(0)

    return {
        event.find(name="a").get("href").split("/")[5]: event.find(name="a").text  # type: ignore[union-attr]
        for event in event_list
    }

async def create_event() -> int:
    """Create an event on the guild website."""
    return 0




