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

        parsed_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find("ul", {"id": "ulOrgs"})

        if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
            NO_ADMIN_DEBUG: Final[str] = (
                "No admin table was found, meaning the token provided "
                "does not have admin access to any societies."
            )
            logger.debug(NO_ADMIN_DEBUG)
            await ctx.respond("The user token provided does not have any admin access!")
            return

        profile_section_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
            response_html,
            "html.parser",
        ).find("div", {"id": "profile_main"})

        if profile_section_html is None:
            logger.warning(
                "Couldn't find the profile section of the user,"
                "when scraping the website's HTML!",
            )
            logger.debug("Retrieved HTML: %s", response_html)
            await ctx.respond(
                "Couldn't find the profile of the user!"
                "This should never happen, please check the logs!",
            )
            return

        user_name: bs4.Tag | bs4.NavigableString | int | None = profile_section_html.find("h1")

        if type(user_name) is not bs4.Tag:
            logger.debug("Found user profile but couldn't find their name!")
            await ctx.respond("Found user profile but couldn't find the name!")
            return

        organisations = [
            list_item.get_text(strip=True)
            for list_item
            in parsed_html.find_all("li")
        ]

        user_name_str: str = user_name.text

        token_message: str = f"Admin token has access to the following MSL Organisations as {user_name_str}:\n{', \n'.join(organisation for organisation in organisations)}"  # noqa: E501

        logger.debug(
            "Admin Token has admin access to: %s as user %s",
            organisations,
            user_name_str,
        )

        await ctx.respond(token_message)
