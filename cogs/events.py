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
from utils import CommandChecks, GoogleCalendar, TeXBotApplicationContext, TeXBotBaseCog

if TYPE_CHECKING:
    import datetime
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

EVENT_LIST_URL: Final[str] = "https://www.guildofstudents.com/events/edit/6531/"
FROM_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtFromDate"
TO_DATE_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$datesFilter$txtToDate"
BUTTON_KEY: Final[str] = "ctl00$ctl00$Main$AdminPageContent$fsSetDates$btnSubmit"
EVENT_TABLE_ID: Final[str] = "ctl00_ctl00_Main_AdminPageContent_gvEvents"


class EventsManagementCommandsCog(TeXBotBaseCog):
    """Cog class to define event management commands."""

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

    async def _get_all_guild_events(self, ctx: TeXBotApplicationContext, from_date: str, to_date: str) -> None:  # noqa: E501
        """Fetch all events on the guild website."""
        data_fields, new_cookies = await self._get_msl_context(url=EVENT_LIST_URL)

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
            cookies=new_cookies,
        )
        async with session_v2, session_v2.post(url=EVENT_LIST_URL, data=data_fields) as http_response:
            if http_response.status != 200:
                await self.command_send_error(
                    ctx=ctx,
                    message="Returned a non-200 status code!!!.",
                )
                logger.debug(http_response)
                return

            response_html: str = await http_response.text()

        event_table_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
                markup=response_html,
                features="html.parser",
            ).find(
                name="table",
                attrs={"id": EVENT_TABLE_ID},
            )

        if event_table_html is None or isinstance(event_table_html, bs4.NavigableString):
            await self.command_send_error(
                ctx=ctx,
                message="Something went wrong and the event list could not be fetched.",
            )
            return

        if "There are no events" in str(event_table_html):
            await ctx.respond(
                content=(
                    f"There are no events found for the date range: {from_date} to {to_date}."
                ),
            )
            logger.debug(event_table_html)
            return

        event_list: list[bs4.Tag] = event_table_html.find_all(name="tr")

        event_list.pop(0)

        event_ids: dict[str, str] = {
            event.find(name="a").get("href").split("/")[5]: event.find(name="a").text  # type: ignore[union-attr]
            for event in event_list
        }

        response_message: str = (
            f"Guild events from {from_date} to {to_date}:\n"
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

        formatted_from_date: str = from_date_dt.strftime("%d/%m/%Y")
        formatted_to_date: str = to_date_dt.strftime("%d/%m/%Y")

        await self._get_all_guild_events(ctx, formatted_from_date, formatted_to_date)

        events: list[dict[str, str]] | None = await GoogleCalendar.fetch_events()

        await ctx.send(content=f"Found GCal events: {events}")

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
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="location",
        description="The location of the event.",
        required=False,
        input_type=str,
        parameter_name="str_location",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def setup_event(self, ctx: TeXBotApplicationContext, str_event_title: str, str_start_date: str, str_start_time: str, str_end_date: str, str_end_time: str, *, str_description: str, str_location: str) -> None:  # noqa: E501, PLR0913
        """
        Definition & callback response of the "delete_all_reminders" command.

        Takes in the title of the event, the start and end dates and times of the event.
        Optionally takes a long description for the event.
        """
        main_guild: discord.Guild = self.bot.main_guild
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

        try:
            new_discord_event: discord.ScheduledEvent | None = await main_guild.create_scheduled_event(  # noqa: E501
                name=str_event_title,
                start_time=start_date_dt,
                end_time=end_date_dt,
                description=str_description if str_description else "No description provided.",
                location=str_location if str_location else "No location provided.",
            )
        except discord.Forbidden:
            await self.command_send_error(
                ctx=ctx,
                message="TeX-Bot does not have the required permissions to create an event.",
            )
            return

        await ctx.respond(f"Event created successful!\n{new_discord_event}")


    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="get-msl-context",
        description="debug command to check the msl context retrieved for a given url",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="url",
        description="The URL to get the MSL context for.",
        required=True,
        input_type=str,
        parameter_name="str_url",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_msl_context(self, ctx: TeXBotApplicationContext, str_url: str) -> None:
        """Command to get the MSL context for a given URL."""
        data_fields, cookies = await self._get_msl_context(str_url)
        logger.debug(data_fields)
        logger.debug(cookies)
        await ctx.respond(
            content=(
                f"Context headers: {data_fields}\n"
                f"Context data: {cookies}"
            ),
        )

