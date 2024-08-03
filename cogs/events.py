"""Contains cog classes for any events interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("EventsManagementCommandsCog",)


import logging
from collections.abc import Mapping
from logging import Logger
from typing import TYPE_CHECKING, Final

import aiohttp
import bs4
import dateutil.parser
import discord
from bs4 import BeautifulSoup
from dateutil.parser import ParserError

from config import settings
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

if TYPE_CHECKING:
    import datetime
    from http.cookies import Morsel

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

    async def _get_msl_context(self, url: str) -> tuple[dict[str, str], dict[str, str]]:
        """Get the required context headers, data and cookies to make a request to MSL."""
        http_session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )
        async with http_session, http_session.get(url) as field_data:
            data_response = BeautifulSoup(await field_data.text(), "html.parser")

        return {}, {}

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

        anti_xss_cookie: Morsel[str] | None = field_data.cookies.get("__AntiXsrfToken")
        if anti_xss_cookie is not None:
            new_cookies["__AntiXsrfToken"] = anti_xss_cookie.value

        asp_net_shared_cookie: Morsel[str] | None = field_data.cookies.get(".AspNet.SharedCookie")  # noqa: E501
        if asp_net_shared_cookie is not None:
            new_cookies[".AspNet.SharedCookie"] = asp_net_shared_cookie.value

        asp_session_id: Morsel[str] | None = field_data.cookies.get("ASP.NET_SessionId")
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

        event_table_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
                response_html,
                "html.parser",
            ).find(
                "table",
                {"id": EVENT_TABLE_ID},
            )

        if event_table_html is None or isinstance(event_table_html, bs4.NavigableString):
            await self.command_send_error(
                ctx,
                message="Something went wrong and the event list could not be fetched.",
            )
            return

        if "There are no events" in str(event_table_html):
            await ctx.respond(
                content=(
                    f"There are no events found for the date range: {from_date} to {to_date}."
                ),
            )
            return

        event_list: list[bs4.Tag] = event_table_html.find_all("tr")

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

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="create-event",
        description="Sets up an event on the Guild website, Discord and Google Calendar.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="event-title",
        description="The title of the event.",
        required=True,
        input_type=str,
        parameter_name="str_event_title",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="start-date",
        description="The date the event starts. Must be in the format `dd/mm/yyyy`.",
        required=True,
        input_type=str,
        parameter_name="str_start_date",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="start-time",
        description="The time the event starts. Must be in the format `hh:mm`.",
        required=True,
        input_type=str,
        parameter_name="str_start_time",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="end-date",
        description="The date the event ends. Must be in the format `dd/mm/yyyy`.",
        required=True,
        input_type=str,
        parameter_name="str_end_date",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="end-time",
        description="The time the event ends. Must be in the format `hh:mm`.",
        required=True,
        input_type=str,
        parameter_name="str_end_time",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="A long description of the event.",
        required=False,
        input_type=str,
        parameter_name="str_description",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def setup_event(self, ctx: TeXBotApplicationContext, str_event_title: str, str_start_date: str, str_start_time: str, str_end_date: str, str_end_time: str, *, str_description: str) -> None:  # noqa: E501
        """
        Definition & callback response of the "delete_all_reminders" command.

        Takes in the title of the event, the start and end dates and times of the event.
        Optionally takes a long description for the event.
        """
        try:
            start_date_dt: datetime.datetime = dateutil.parser.parse(
                f"{str_start_date}T{str_start_time}", dayfirst=True,
            )
            end_date_dt: datetime.datetime = dateutil.parser.parse(
                f"{str_end_date}T{str_end_time}", dayfirst=True,
            )
        except ParserError:
            await ctx.respond(
                content=(
                    ":warning: Invalid date format. "
                    "Please use the format `dd/mm/yyyy` for dates and `hh:mm` for times."
                ),
            )
            return

        if start_date_dt > end_date_dt:
            await ctx.respond(
                content=(
                    f":warning: Start dt ({start_date_dt}) "
                    f"is after end dt ({end_date_dt})."
                ),
            )
            return

        await ctx.respond(content=f"Got DTs: {start_date_dt} and {end_date_dt}.")




