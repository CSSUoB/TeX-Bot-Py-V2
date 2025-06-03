"""Module for fetching reports from the guild website."""

import logging
import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING

import aiohttp
import anyio

from .core import (
    BASE_HEADERS,
    CURRENT_YEAR_END_DATE,
    CURRENT_YEAR_START_DATE,
    ORGANISATION_ID,
    get_msl_context,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

__all__: "Sequence[str]" = (
    "get_product_customisations",
    "get_product_sales",
    "update_current_year_sales_report",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


SALES_REPORTS_URL: "Final[str]" = (
    f"https://www.guildofstudents.com/organisation/salesreports/{ORGANISATION_ID}/"
)
SALES_FROM_DATE_KEY: "Final[str]" = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtFromDate"
SALES_FROM_TIME_KEY: "Final[str]" = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtFromTime"
SALES_TO_DATE_KEY: "Final[str]" = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtToDate"
SALES_TO_TIME_KEY: "Final[str]" = "ctl00$ctl00$Main$AdminPageContent$drDateRange$txtToTime"


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


async def fetch_report_url_and_cookies(
    report_type: ReportType, *, from_date: datetime, to_date: datetime
) -> tuple[str | None, dict[str, str]]:
    """Fetch the specified report from the guild website."""
    data_fields, cookies = await get_msl_context(url=SALES_REPORTS_URL)

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
    async with (
        session_v2,
        session_v2.post(url=SALES_REPORTS_URL, data=data_fields) as http_response,
    ):
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
    report_url, cookies = await fetch_report_url_and_cookies(
        report_type=ReportType.SALES,
        to_date=CURRENT_YEAR_END_DATE,
        from_date=CURRENT_YEAR_START_DATE,
    )

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
                product_id: bytes = (
                    product_name_and_id.split(b" ")[0].removeprefix(b"[")
                ).removesuffix(b"]")
                product_name: bytes = b" ".join(
                    product_name_and_id.split(b" ")[1:],
                )
                date: bytes = values[5]
                quantity: bytes = values[6]
                unit_price: bytes = values[7]
                total: bytes = values[8]

                await report_file.write(
                    product_id
                    + b","
                    + product_name
                    + b","
                    + date
                    + b","
                    + quantity
                    + b","
                    + unit_price
                    + b","
                    + total
                    + b"\n",
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


async def get_product_customisations(product_id: str) -> list[dict[str, str]]:
    """Get the set of product customisations for a given product ID, checking the past year."""
    report_url, cookies = await fetch_report_url_and_cookies(
        report_type=ReportType.CUSTOMISATION,
        to_date=datetime.now(tz=timezone.utc),  # noqa: UP017
        from_date=datetime.now(tz=timezone.utc) - timedelta(weeks=52),  # noqa: UP017
    )

    if report_url is None:
        logger.warning("Failed to retrieve customisations report URL.")
        return []

    customisation_records: list[dict[str, str]] = []
    file_session: aiohttp.ClientSession = aiohttp.ClientSession(
        headers=BASE_HEADERS,
        cookies=cookies,
    )
    async with file_session, file_session.get(url=report_url) as file_response:
        if file_response.status != 200:
            logger.warning("Customisation report file session returned a non 200 status code.")
            logger.debug(file_response)
            return []

        for line in (await file_response.content.read()).split(b"\n")[7:]:
            if line == b"\r" or not line:
                break

            values: list[str] = line.decode("utf-8").split(",")

            if len(values) < 6:
                logger.debug("Invalid line in customisations report!")
                logger.debug(values)
                continue

            product_name_and_id: str = values[0]
            file_product_id: str = (
                product_name_and_id.split(" ")[0].removeprefix("[").removesuffix("]")
            )
            file_product_name: str = " ".join(product_name_and_id.split(" ")[1:])

            if file_product_id != product_id:
                continue

            purchase_id: str = values[1]
            purchase_date: str = values[2]

            student_id: str = values[3]
            customisation_name: str = values[4]
            customisation_value: str = values[5]

            for item in customisation_records:
                if item["purchase_id"] == purchase_id:
                    item[customisation_name] = customisation_value
                    logger.debug(item)
                    break

                customisation_records.append(
                    {
                        "product_id": product_id,
                        "product_name": file_product_name,
                        "purchase_id": purchase_id,
                        "purchase_date": purchase_date,
                        "student_id": student_id,
                        customisation_name: customisation_value,
                    },
                )

    return customisation_records
