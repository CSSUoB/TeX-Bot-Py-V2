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
from utils import CommandChecks, GoogleCalendar, TeXBotApplicationContext, TeXBotBaseCog, msl

if TYPE_CHECKING:
    import datetime

logger: Final[Logger] = logging.getLogger("TeX-Bot")


BASE_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

BASE_COOKIES: Final[Mapping[str, str]] = {
    ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
}

class EventsManagementCommandsCog(TeXBotBaseCog):
    """Cog class to define event management commands."""

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
        formatted_to_date: str = to_date_dt.strftime(format="%d/%m/%Y")

        await self._get_all_guild_events(ctx, formatted_from_date, formatted_to_date)

        events: list[dict[str, str]] | None = await GoogleCalendar.fetch_events()

        if events is None:
            await ctx.send(content="No events found on the Google Calendar.")
            return

        events_message: str = (
            f"Found {len(events)} events on the Google Calendar:\n"
            + "\n".join(
                f"{event['event_title']} - {event['start_dt']} to {event['end_dt']}"
                for event in events
            )
        )

        await ctx.send(content=events_message)

        scheduled_events_list: list[discord.ScheduledEvent] = await ctx.guild.fetch_scheduled_events()  # noqa: E501

        scheduled_events_message: str = (
            f"Found {len(scheduled_events_list)} scheduled events on the Discord server:\n"
            + "\n".join(
                f"{event.id} - {event.name} - {event.start_time} to {event.end_time}"
                for event in scheduled_events_list
            )
        )

        await ctx.send(content=scheduled_events_message)



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
                timestr=f"{str_start_date}T{str_start_time}", dayfirst=True,
            )
            end_date_dt: datetime.datetime = dateutil.parser.parse(
                timestr=f"{str_end_date}T{str_end_time}", dayfirst=True,
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

        location: str = str_location if str_location else "No location provided."
        description: str = str_description if str_description else "No description provided."

        try:
            new_discord_event: discord.ScheduledEvent | None = await main_guild.create_scheduled_event(  # noqa: E501
                name=str_event_title,
                start_time=start_date_dt,
                end_time=end_date_dt,
                description=description,
                location=location,
            )
        except discord.Forbidden:
            await self.command_send_error(
                ctx=ctx,
                message="TeX-Bot does not have the required permissions to create a discord event.",  # noqa: E501
            )

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

