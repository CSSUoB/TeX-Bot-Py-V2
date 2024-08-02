"""Contains cog classes for any events interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("EventsManagementCommandsCog",)


import logging
from collections.abc import Mapping
from logging import Logger
from typing import Final

import aiohttp
import bs4
import dateutil.parser
from dateutil.parser import ParserError
import discord
from bs4 import BeautifulSoup

from config import settings
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Final[Logger] = logging.getLogger("TeX-Bot")


REQUEST_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

REQUEST_COOKIES: Final[Mapping[str, str]] = {
    ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
}

REQUEST_URL: Final[str] = "https://www.guildofstudents.com/events/edit/6531/"
FROM_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtFromDate"
TO_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtToDate"
BUTTON_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$fsSetDates$btnSubmit"
EVENT_TABLE_ID: Final[str] = "ctl00_ctl00_Main_AdminPageContent_gvEvents"


class EventsManagementCommandsCog(TeXBotBaseCog):
    """Cog class to define event management commands."""

    async def _get_all_guild_events(self, ctx: TeXBotApplicationContext, from_date: str, to_date: str) -> None:  # noqa: E501
        """Fetch all events on the guild website."""
        form_data: dict[str, str] = {
            FROM_DATE_KEY: from_date,
            TO_DATE_KEY: to_date,
            BUTTON_KEY: "Find Events",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATEENCRYPTED": "",
        }
        http_session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )
        async with http_session, http_session.get(REQUEST_URL) as field_data:
            data_response = BeautifulSoup(await field_data.text(), "html.parser")
            view_state: str = data_response.find("input", {"name": "__VIEWSTATE"}).get("value")  # type: ignore[union-attr, assignment]
            event_validation: str = data_response.find("input", {"name": "__EVENTVALIDATION"}).get("value")  # type: ignore[union-attr, assignment]  # noqa: E501
            view_state_generator: str = data_response.find("input", {"name": "__VIEWSTATEGENERATOR"}).get("value")  # type: ignore[union-attr, assignment]  # noqa: E501

        form_data["__VIEWSTATE"] = view_state
        form_data["__EVENTVALIDATION"] = event_validation
        form_data["__VIEWSTATEGENERATOR"] = view_state_generator

        new_cookies: dict[str, str] = {
            ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
        }

        anti_xss_cookie = field_data.cookies.get("__AntiXsrfToken")
        if anti_xss_cookie is not None:
            new_cookies["__AntiXsrfToken"] = anti_xss_cookie.value

        asp_net_shared_cookie = field_data.cookies.get(".AspNet.SharedCookie")
        if asp_net_shared_cookie is not None:
            new_cookies[".AspNet.SharedCookie"] = asp_net_shared_cookie.value

        asp_session_id = field_data.cookies.get("ASP.NET_SessionId")
        if asp_session_id is not None:
            new_cookies["ASP.NET_SessionId"] = asp_session_id.value

        session_v2: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=new_cookies,
        )
        async with session_v2, session_v2.post(REQUEST_URL, data=form_data) as http_response:
            if http_response.status != 200:
                await self.command_send_error(
                    ctx,
                    message="Returned a non-200 status code!!!.",
                )
                logger.debug(http_response)
                return

            response_html: str = await http_response.text()

        parsed_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
                response_html,
                "html.parser",
            ).find(
                "table",
                {"id": EVENT_TABLE_ID},
            )

        if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
            await self.command_send_error(
                ctx,
                message="Something went wrong and the event list could not be fetched.",
            )
            return

        if "There are no events" in str(parsed_html):
            await ctx.respond(
                content=(
                    f"There are no events found for the date range: {from_date} to {to_date}."
                ),
            )
            return

        event_list: list[bs4.Tag] = parsed_html.find_all("tr")

        event_list.pop(0)

        event_ids: dict[str, str] = {
            event.find("a").get("href").split("/")[5]: event.find("a").text  # type: ignore[union-attr]
            for event in event_list
        }

        response_message: str = (
            f"Events from {from_date} to {to_date}:\n"
            + "\n".join(
                f"{event_id}: {event_name}"
                for event_id, event_name in event_ids.items()
            )
        )

        await ctx.respond(content=response_message)


    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="get-events",
        description="Returns all events currently on the guild website.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="from-date",
        description="The date to start searching from.",
        required=False,
        input_type=str,
        parameter_name="str_from_date",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="to-date",
        description="The date to stop searching at.",
        required=False,
        input_type=str,
        parameter_name="str_to_date",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_events(self, ctx: TeXBotApplicationContext, *, str_from_date: str, str_to_date: str) -> None:  # noqa: E501
        """Command to get the events on the guild website."""
        try:
            if str_from_date:
                from_date_dt = dateutil.parser.parse(str_from_date, dayfirst=True)
            else:
                from_date_dt = dateutil.parser.parse("01/08/2024", dayfirst=True)

            if str_to_date:
                to_date_dt = dateutil.parser.parse(str_to_date, dayfirst=True)
            else:
                to_date_dt = dateutil.parser.parse("31/07/2025", dayfirst=True)
        except ParserError:
            await ctx.respond(
                content=(
                    ":warning: Invalid date format. Please use the format `dd/mm/yyyy`."
                ),
            )
            return

        if from_date_dt > to_date_dt:
            await ctx.respond(
                content=(
                    f":warning: Start date ({from_date_dt}) is after end date ({to_date_dt})."
                ),
            )

        formatted_from_date = from_date_dt.strftime("%d/%m/%Y")
        formatted_to_date = to_date_dt.strftime("%d/%m/%Y")


        await self._get_all_guild_events(ctx, formatted_from_date, formatted_to_date)




