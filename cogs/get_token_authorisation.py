"""Contains cog classes for token authorisation check interactions."""

import logging
from typing import TYPE_CHECKING

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup

from config import settings
from exceptions.does_not_exist import GuestRoleDoesNotExistError
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("GetTokenAuthorisationCommandCog",)

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


class GetTokenAuthorisationCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/get_token_authorisation" command."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="get-token-authorisation",
        description="Checks the authorisations held by the token.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_token_authorisation(self, ctx: "TeXBotApplicationContext") -> None:
        """
        Definition of the "get_token_authorisation" command.

        The "get_token_authorisation" command will retrieve the profile for the token user.
        The profile page will contain the user's name and a list of the MSL organisations
        the user has administrative access to.
        """
        http_session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )

        async with http_session, http_session.get(REQUEST_URL) as http_response:
            response_html: str = await http_response.text()

        page_title: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find("title")

        if not page_title:
            await self.command_send_error(
                ctx=ctx,
                message="Profile page returned no content when checking token authorisation!",
            )
            return

        if (
            (isinstance(page_title, bs4.NavigableString) and "Login" in page_title)
            or
            ("Login" in page_title.string)  # type: ignore[union-attr, operator]
        ):
            BAD_TOKEN_MESSAGE: Final[str] = (
                "Unable to fetch profile page because the token was not valid."  # noqa: S105
            )
            logger.warning(BAD_TOKEN_MESSAGE)
            await ctx.respond(content=BAD_TOKEN_MESSAGE)
            return

        profile_section_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find("div", {"id": "profile_main"})

        if profile_section_html is None:
            logger.warning(
                "Couldn't find the profile section of the user"
                "when scraping the website's HTML!",
            )
            logger.debug("Retrieved HTML: %s", response_html)
            await ctx.respond(
                "Couldn't find the profile of the user! "
                "This should never happen, please check the logs!",
            )
            return

        user_name: bs4.Tag | bs4.NavigableString | int | None = profile_section_html.find("h1")

        if not isinstance(user_name, bs4.Tag):
            NO_PROFILE_DEBUG_MESSAGE: Final[str] = (
                "Found user profile but couldn't find their name!"
            )
            logger.debug(NO_PROFILE_DEBUG_MESSAGE)
            await ctx.respond(NO_PROFILE_DEBUG_MESSAGE)
            return

        parsed_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find("ul", {"id": "ulOrgs"})

        if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
            NO_ADMIN_TABLE_MESSAGE: Final[str] = (
                f"Failed to retrieve the admin table for user: {user_name.string}."
                "Please check you have used the correct token!"
            )
            logger.warning(NO_ADMIN_TABLE_MESSAGE)
            await ctx.respond(content=NO_ADMIN_TABLE_MESSAGE)
            return

        organisations: Iterable[str] = [
            list_item.get_text(strip=True) for list_item in parsed_html.find_all("li")
        ]

        logger.debug(
            "Admin Token has admin access to: %s as user %s",
            organisations,
            user_name.text,
        )

        await ctx.respond(
            f"Admin token has access to the following MSL Organisations as "
            f"{user_name.text}:\n{', \n'.join(
                organisation for organisation in organisations
            )}",
            ephemeral=False,
        )
