"""Functions to enable interaction with MSL based SU websites."""

from collections.abc import Sequence

__all__: Sequence[str] = ()


import logging
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Final

import aiohttp
import anyio
import bs4
from bs4 import BeautifulSoup

from config import settings

if TYPE_CHECKING:
    from http.cookies import Morsel


logger: Final[Logger] = logging.getLogger("TeX-Bot")


BASE_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

BASE_COOKIES: Final[Mapping[str, str]] = {
    ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
}

MEMBER_HTML_TABLE_IDS: Final[frozenset[str]] = frozenset(
    {
        "ctl00_Main_rptGroups_ctl05_gvMemberships",
        "ctl00_Main_rptGroups_ctl03_gvMemberships",
    },
)

ORGANISATION_ID: Final[str] = settings["MSL_ORGANISATION_ID"]

EVENT_LIST_URL: Final[str] = f"https://www.guildofstudents.com/events/edit/{ORGANISATION_ID}/"
CREATE_EVENT_URL: Final[str] = f"https://www.guildofstudents.com/events/edit/event/{ORGANISATION_ID}/"
MEMBERS_LIST_URL: Final[str] = f"https://guildofstudents.com/organisation/memberlist/{ORGANISATION_ID}/?sort=groups"
SALES_REPORTS_URL: Final[str] = f"https://www.guildofstudents.com/organisation/salesreports/{ORGANISATION_ID}/"


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


EVENTS_FROM_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtFromDate"
EVENTS_TO_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtToDate"
EVENTS_BUTTON_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$fsSetDates$btnSubmit"
EVENTS_TABLE_ID: Final[str] = "ctl00_ctl00_Main_AdminPageContent_gvEvents"

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

    event_ids: dict[str, str] = {
        event.find(name="a").get("href").split("/")[5]: event.find(name="a").text  # type: ignore[union-attr]
        for event in event_list
    }

    return event_ids


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
        member.find_all(name="td")[1].text.strip(),  # NOTE: This will not properly handle external members who do not have an ID...
        )
        for member in standard_members + all_members
    }

    return member_list

async def is_student_id_member(student_id: str | int) -> bool:
    """Check if the student ID is a member of the society."""
    all_ids: set[str] = {
        str(member[1]) for member in await get_full_membership_list()
    }

    return str(student_id) in all_ids


SALES_FROM_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtFromDate"
SALES_FROM_TIME_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtFromTime"
SALES_TO_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtToDate"
SALES_TO_TIME_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtToTime"


class ReportType(Enum):
    """
    Enum to define the different types of reports available.

    SALES - Provides a report of sales by product, date and quantity.
    CUSTOMISATION - Provides a report of customisations by product, date and quantity.

    MSL also supports "Purchasers" reports, however, these are largely unused but could
    be implemented in the future.
    """

    SALES = "Sales"
    CUSTOMISATION = "Customisations"


async def fetch_report_url_and_cookies(report_type: ReportType) -> tuple[str | None, dict[str, str]]:  # noqa: E501
    """Fetch the specified report from the guild website."""
    data_fields, cookies = await get_msl_context(url=SALES_REPORTS_URL)

    from_date: datetime = datetime(year=datetime.now(tz=timezone.utc).year, month=7, day=1, tzinfo=timezone.utc)  # noqa: E501, UP017
    to_date: datetime = datetime(year=datetime.now(tz=timezone.utc).year + 1, month=6, day=30, tzinfo=timezone.utc)  # noqa: E501, UP017

    form_data: dict[str, str] = {
        SALES_FROM_DATE_KEY: from_date.strftime("%d/%m/%Y"),
        SALES_FROM_TIME_KEY: from_date.strftime("%H:%M"),
        SALES_TO_DATE_KEY: to_date.strftime("%d/%m/%Y"),
        SALES_TO_TIME_KEY: to_date.strftime("%H:%M"),
        "__EVENTTARGET": f"ctl00$ctl00$Main$AdminPageContent$lb{report_type.value}",
        "__EVENTARGUMENT": "",
        "__VIEWSTATEENCRYPTED": "",
    }

    data_fields.pop("ctl00$ctl00$search$btnSubmit")

    data_fields.update(form_data)

    session_v2: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=cookies,
    )
    async with session_v2, session_v2.post(url=SALES_REPORTS_URL, data=data_fields) as http_response:  # noqa: E501
        if http_response.status != 200:
            logger.debug("Returned a non 200 status code!!")
            logger.debug(http_response)
            return None, {}

        response_html: str = await http_response.text()

    if "no transactions" in response_html:
        logger.debug("No transactions were found!")
        return None, {}

    match = re.search(r'ExportUrlBase":"(.*?)"', response_html)
    if not match:
        logger.warning("Failed to find the report export url from the http response.")
        logger.debug(response_html)
        return None, {}

    urlbase: str = match.group(1).replace(r"\u0026", "&").replace("\\/", "/")
    if not urlbase:
        logger.warning("Failed to construct report url!")
        logger.debug(match)
        return None, {}

    return f"https://guildofstudents.com/{urlbase}CSV", cookies


async def update_current_year_sales_report() -> None:
    """Get all sales reports from the guild website."""
    report_url, cookies = await fetch_report_url_and_cookies(report_type=ReportType.SALES)

    if report_url is None:
        logger.debug("No report URL was found!")
        return

    file_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=cookies,
    )
    async with file_session, file_session.get(url=report_url) as file_response:
        if file_response.status != 200:
            logger.warning("Returned a non 200 status code!!")
            logger.debug(file_response)
            return

        async with await anyio.open_file("CurrentYearSalesReport.csv", "wb") as report_file:
            await report_file.write(
                b"product_id,product_name,date,quantity,unit_price,total\n",
            )

            for line in (await file_response.read()).split(b"\n")[7:]:
                if line == b"\r" or not line:
                    break

                values: list[bytes] = line.split(b",")

                product_name_and_id: bytes = values[0]
                product_id: bytes = ((
                        product_name_and_id.split(b" ")[0].removeprefix(b"[")
                    ).removesuffix(b"]")
                )
                product_name: bytes = b" ".join(
                    product_name_and_id.split(b" ")[1:],
                )
                date: bytes = values[5]
                quantity: bytes = values[6]
                unit_price: bytes = values[7]
                total: bytes = values[8]

                await report_file.write(
                    product_id + b"," +
                    product_name + b"," +
                    date + b"," +
                    quantity + b"," +
                    unit_price + b"," +
                    total + b"\n",
                )

            logger.debug("Sales report updated successfully!!")
            return


async def get_product_sales(product_id: str) -> dict[str, int]:
    """Get the dates and quantities of sales for a given product ID."""
    product_sales_data: dict[str, int] = {}
    async with await anyio.open_file("CurrentYearSalesReport.csv", "r") as report_file:
        for line in (await report_file.readlines())[1:]:
            values: list[str] = line.split(",")

            if values[0] == product_id:
                product_sales_data[values[2]] = int(values[3])

    return product_sales_data
