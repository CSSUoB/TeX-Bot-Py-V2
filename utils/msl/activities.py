"""Module for fetching activities from the guild website."""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Final

import aiohttp
import bs4
from bs4 import BeautifulSoup

from .core import BASE_HEADERS, ORGANISATION_ID, get_msl_context

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from logging import Logger

__all__: "Sequence[str]" = ()

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


ACTIVITIES_URL: Final[str] = (
    f"https://www.guildofstudents.com/organisation/admin/activities/all/{ORGANISATION_ID}/"
)

ACTIVITIES_BUTTON_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$fsFilter$btnSubmit"
ACTIVITIES_TABLE_ID: Final[str] = "ctl00_ctl00_Main_AdminPageContent_gvResults"
ACTIVITIES_START_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$drDates$txtFromDate"
ACTIVITIES_END_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$drDates$txtToDate"


class ActivityStatus(Enum):
    """
    Enum to define the possible activity status values.

    Submitted - The activity has been submitted and is pending approval.
    Approved - The activity has been approved and is scheduled.
    Draft - The activity is a draft and is not yet submitted.
    Cancelled - The activity has been cancelled.
    Queried - The activity has been queried and is pending response.
    """

    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    DRAFT = "Draft"
    CANCELLED = "Cancelled"
    QUERIED = "Queried"


async def fetch_guild_activities(from_date: "datetime", to_date: "datetime") -> dict[str, str]:
    """Fetch all activities on the guild website."""
    data_fields, cookies = await get_msl_context(url=ACTIVITIES_URL)

    form_data: dict[str, str] = {
        ACTIVITIES_START_DATE_KEY: from_date.strftime("%d/%m/%Y"),
        ACTIVITIES_END_DATE_KEY: to_date.strftime("%d/%m/%Y"),
        ACTIVITIES_BUTTON_KEY: "Apply",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATEENCRYPTED": "",
    }

    data_fields.update(form_data)

    data_fields.pop("ctl00$ctl00$Main$AdminPageContent$fsFilter$btnCancel")

    session_v2: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=cookies,
    )
    async with (
        session_v2,
        session_v2.post(url=ACTIVITIES_URL, data=data_fields) as http_response,
    ):
        if http_response.status != 200:
            logger.debug("Returned a non 200 status code!!")
            logger.debug(http_response)
            return {}

        response_html: str = await http_response.text()

    activities_table_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
        markup=response_html,
        features="html.parser",
    ).find(
        name="table",
        attrs={"id": ACTIVITIES_TABLE_ID},
    )

    if activities_table_html is None or isinstance(activities_table_html, bs4.NavigableString):
        logger.warning("Failed to find the activities table.")
        logger.debug(response_html)
        return {}

    if "There are no activities" in str(activities_table_html):
        logger.debug("No activities were found matching the date range.")
        return {}

    activities_list: list[bs4.Tag] = activities_table_html.find_all(name="tr")

    activities_list.pop(0)

    return {
        activity.find(name="a").get("href").split("/")[7]: activity.find_all(name="td")[
            1
        ].text.strip()  # type: ignore[union-attr]
        for activity in activities_list
    }


async def create_activity() -> int:
    """Create an activity on the guild website."""
    return 0


async def fetch_activity(activity_id: int) -> dict[str, str]:
    """Fetch a specific activity from the guild website."""
    raise NotImplementedError
