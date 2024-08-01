"""Contains cog classes for any events interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("EventsManagementCommandsCog",)


import logging
from collections.abc import Mapping
from logging import Logger
from typing import Final

import aiohttp
import bs4
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

    async def _get_all_guild_events(self, ctx: TeXBotApplicationContext) -> None:
        """Fetch all events on the guild website."""
        form_data: dict[str, str] = {
            FROM_DATE_KEY: "01/01/2024",
            TO_DATE_KEY: "01/01/2025",
            BUTTON_KEY: "Find Events",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
        }
        http_session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )
        async with http_session, http_session.get(REQUEST_URL) as field_data:
            data_response = BeautifulSoup(await field_data.text(), "html.parser")
            view_state: str = data_response.find("input", {"name": "__VIEWSTATE"}).get("value")  # type: ignore[union-attr, assignment]
            event_validation: str = data_response.find("input", {"name": "__EVENTVALIDATION"}).get("value")  # type: ignore[union-attr, assignment]  # noqa: E501

        form_data["__VIEWSTATE"] = view_state
        form_data["__EVENTVALIDATION"] = event_validation

        session_v2: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )
        async with session_v2, session_v2.post(REQUEST_URL, data=form_data) as http_response:
            if http_response.headers.get("Content-Type") == "gzip":
                response_html = await http_response.read()
            else:
                response_html = await http_response.text()

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
            logger.debug(http_response)
            return

        if "There are no events" in str(parsed_html):
            await ctx.respond("There are no events found for the date range selected.")
            logger.debug(http_response.request_info)
            return

        await ctx.respond(parsed_html)

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="get-events",
        description="Returns all events currently on the guild website.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_events(self, ctx: TeXBotApplicationContext) -> None:
        """Command to get the events on the guild website."""
        await self._get_all_guild_events(ctx)




