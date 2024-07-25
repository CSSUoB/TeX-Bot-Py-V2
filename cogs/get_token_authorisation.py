"""Contains cog classes for token authorisation check interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("GetTokenAuthorisationCommand",)


import contextlib
import logging
from collections.abc import Iterable, Mapping
from logging import Logger
from typing import Final

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup

from config import settings
from exceptions.does_not_exist import GuestRoleDoesNotExistError
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Final[Logger] = logging.getLogger("TeX-Bot")

REQUEST_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

REQUEST_COOKIES: Final[Mapping[str, str]] = {
    ".ASPXAUTH": settings["MEMBERS_LIST_URL_SESSION_COOKIE"],
}

REQUEST_URL: Final[str] = "https://guildofstudents.com/profile"


class GetTokenAuthorisationCommand(TeXBotBaseCog):
    """Cog class that defines the "/get_token_authorisation" command."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="get-token-authorisation",
        description="Checks the authorisations held by the token.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_token_authorisation(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition of the "get_token_authorisation" command.

        The "get_token_authorisation" command will retrieve the profle for the token user.
        The profile page will contain the user's name and a list of the MSL organisations
        the user has administrative access to.
        """
        http_session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
        )

        async with http_session, http_session.get(REQUEST_URL) as http_response:
            response_html: str = await http_response.text()

        parsed_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find("ul", {"id": "ulOrgs"})

        if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
            logger.debug(
                "No admin table was found, meaning the token provided "
                "does not have admin access to any societies.",
            )
            await ctx.respond("The user token provided does not have any admin access!")
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

        organisations: Iterable[str] = [
            list_item.get_text(strip=True) for list_item in parsed_html.find_all("li")
        ]

        logger.debug(
            "Admin Token has admin access to: %s as user %s",
            organisations,
            user_name.text,
        )

        guest_role: discord.Role | None = None
        with contextlib.suppress(GuestRoleDoesNotExistError):
            guest_role = await ctx.bot.guest_role

        await ctx.respond(
            f"Admin token has access to the following MSL Organisations as "
            f"{user_name.text}:\n{', \n'.join(
                organisation for organisation in organisations
            )}",
            ephemeral=bool(
                (not guest_role) or ctx.channel.permissions_for(guest_role).is_superset(
                    discord.Permissions(view_channel=True),
                ),
            ),
        )
