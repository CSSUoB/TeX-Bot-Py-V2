"""Contains cog classes for token authorisation check interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("GetTokenAuthorisationCommand",)


import logging
from logging import Logger
from typing import Final

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup

from config import settings
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")


class GetTokenAuthorisationCommand(TeXBotBaseCog):
    """Cog class that defines the "/get_token_authorisation" command."""

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="get-token-authorisation",
        description="Checks the authorisations held by the token.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_token_authorisation(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition of the "get_token_authorisation" command.

        The command will retrieve the profle for the user who owns the token.
        The profile page will contain the user's name and a list of the MSL organisations
        the user has administrative access to.
        """
        request_headers: dict[str, str] = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        request_cookies: dict[str, str] = {
            ".ASPXAUTH": settings["MEMBERS_LIST_URL_SESSION_COOKIE"],
        }

        REQUEST_URL: Final[str] = "https://guildofstudents.com/profile"

        async with aiohttp.ClientSession(headers=request_headers, cookies=request_cookies) as http_session:  # noqa: E501, SIM117
            async with http_session.get(REQUEST_URL) as http_response:
                response_html: str = await http_response.text()

        TABLE_ID: str = "ulOrgs"
        parsed_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find(
            "ul",
            {"id": TABLE_ID},
        )

        if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
            NO_ADMIN_DEBUG: Final[str] = (
                "No admin table was found, meaning the token provided "
                "does not have admin access to any societies."
            )
            logger.debug(NO_ADMIN_DEBUG)
            await ctx.respond("The user token provided does not have any admin access!")
            return

        orgs = [li.get_text(strip=True) for li in parsed_html.find_all("li")]

        DIV_ID: Final[str] = "profile_main"
        profile_section: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find(
            "div",
            {"id": DIV_ID},
        )

        if profile_section is None:
            logger.warning("Couldn't find the profile of the user!")
            logger.debug(response_html)
            await ctx.respond(
                "Couldn't find the profile of the user!"
                "This should never happen, please check the logs!",
            )
            return

        user_name: bs4.Tag | bs4.NavigableString | int | None = profile_section.find("h1")

        if type(user_name) is not bs4.Tag:
            logger.debug("Found user profile but couldn't find their name!")
            await ctx.respond("Found user profile but couldn't find the name!")
            return

        user_name_str: str = user_name.text

        token_message: str = f"Admin token has access to the following MSL Organisations as {user_name_str}:\n{', \n'.join(org for org in orgs)}"  # noqa: E501

        logger.debug("Admin Token has admin access to: %s as user %s", orgs, user_name_str)
        await ctx.respond(token_message)



