"""Contains cog classes for token authorisation check interactions."""

import logging
from typing import TYPE_CHECKING, override

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup
from discord.ext import tasks

from config import settings
from utils import CommandChecks, TeXBotBaseCog
from utils.error_capture_decorators import (
    capture_guild_does_not_exist_error,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBot, TeXBotApplicationContext

__all__: "Sequence[str]" = ("GetTokenAuthorisationCommandCog","TokenAuthorisationCheckTaskCog")

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

REQUEST_HEADERS: "Final[Mapping[str, str]]" = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

REQUEST_COOKIES: "Final[Mapping[str, str]]" = {
    ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
}

REQUEST_URL: "Final[str]" = "https://guildofstudents.com/profile"


class TokenAuthorisationBaseCog(TeXBotBaseCog):
    """Cog class that defines the base for token authorisation functions."""

    async def is_token_valid(self) -> bool:
        """
        Definition of method to check if the authorisation token is valid.

        This is done by requesting the user profile page and
        checking if the page title contains "Login".
        """
        http_session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )

        async with http_session, http_session.get(REQUEST_URL) as http_response:
            response_html: str = await http_response.text()

        response_object: bs4.BeautifulSoup = BeautifulSoup(
            response_html,
            "html.parser",
        )

        page_title: bs4.Tag | bs4.NavigableString | None = response_object.find("title")

        return "Login" in str(page_title)

    async def get_token_groups(self, iterable: bool) -> str | "Iterable"[str]:  # noqa: FBT001
        """
        Definition of method to get the groups the token has access to.

        This is done by requesting the user profile page and
        scraping the HTML for the list of groups.
        """
        http_session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )

        async with http_session, http_session.get(REQUEST_URL) as http_response:
            response_html: str = await http_response.text()

        response_object: bs4.BeautifulSoup = BeautifulSoup(
            response_html,
            "html.parser",
        )

        page_title: bs4.Tag | bs4.NavigableString | None = response_object.find("title")

        if not page_title:
            PROFILE_PAGE_INVALID: Final[str] = (
                "Profile page returned no content when checking token authorisation."
            )
            logger.warning(PROFILE_PAGE_INVALID)
            return PROFILE_PAGE_INVALID

        if "Login" in str(page_title):
            logger.warning("Unable to fetch profile page because the token was not valid.")
            return []

        profile_section_html: bs4.Tag | bs4.NavigableString | None = response_object.find(
            "div",
            {"id": "profile_main"},
        )

        if profile_section_html is None:
            logger.warning(
                "Couldn't find the profile section of the user"
                "when scraping the website's HTML!",
            )
            logger.debug("Retrieved HTML: %s", response_html)
            return "Something went wrong when fetching the profile page!"

        user_name: bs4.Tag | bs4.NavigableString | int | None = profile_section_html.find("h1")

        if not isinstance(user_name, bs4.Tag):
            NO_PROFILE_DEBUG_MESSAGE: Final[str] = (
                "Found user profile but couldn't find their name!"
            )
            logger.warning(NO_PROFILE_DEBUG_MESSAGE)
            logger.debug("Retrieved HTML: %s", response_html)
            return "Something went wrong when fetching the profile page!"

        parsed_html: bs4.Tag | bs4.NavigableString | None = response_object.find(
            "ul",
            {"id": "ulOrgs"},
        )

        if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
            NO_ADMIN_TABLE_MESSAGE: Final[str] = (
                f"Failed to retrieve the admin table for user: {user_name.string}."
                "Please check you have used the correct token!"
            )
            logger.warning(NO_ADMIN_TABLE_MESSAGE)
            return NO_ADMIN_TABLE_MESSAGE

        organisations: Iterable[str] = [
            list_item.get_text(strip=True) for list_item in parsed_html.find_all("li")
        ]

        logger.debug(
            "Admin Token has admin access to: %s as user %s",
            organisations,
            user_name.text,
        )

        constructed_organisations: str = (
            f"Admin token has access to the following MSL Organisations as "
            f"{user_name.text}:\n{', \n'.join(organisation for organisation in organisations)}"
        )

        return organisations if iterable else constructed_organisations


class GetTokenAuthorisationCommandCog(TokenAuthorisationBaseCog):
    """Cog class that defines the "/get_token_authorisation" command."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="get-token-authorisation",
        description="Checks the authorisations held by the token.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_token_authorisation(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """
        Definition of the "get_token_authorisation" command.

        The "get_token_authorisation" command will retrieve the profile for the token user.
        The profile page will contain the user's name and a list of the MSL organisations
        the user has administrative access to.
        """
        await ctx.defer(ephemeral=True)
        async with ctx.typing():
            await ctx.followup.send(
                content=str(await self.get_token_groups(iterable=False)),
                ephemeral=True,
            )


class TokenAuthorisationCheckTaskCog(TokenAuthorisationBaseCog):
    """Cog class that defines the background task for token authorisation checks."""

    @override
    def __init__(self, bot: "TeXBot") -> None:
        """Start all task managers when this cog is initialised."""
        if settings["AUTO_AUTH_SESSION_COOKIE_CHECKING"]:
            _ = self.token_authorisation_check_task.start()

        super().__init__(bot)

    @override
    def cog_unload(self) -> None:
        """
        Unload-hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.token_authorisation_check_task.cancel()

    @tasks.loop(**settings["AUTO_AUTH_SESSION_COOKIE_CHECKING"])
    @capture_guild_does_not_exist_error
    async def token_authorisation_check_task(self) -> None:
        """
        Definition of the background task that checks the token authorisation.

        The task will check if the token is valid and if it is, it will retrieve the
        groups the token has access to.
        """
        logger.debug("Running token authorisation check task...")

        token_valid: bool = await self.is_token_valid()

        if not token_valid:
            logger.warning("Token is not valid!")

            await self.bot.fetch_log_channel().send("Auth token has expired!")
