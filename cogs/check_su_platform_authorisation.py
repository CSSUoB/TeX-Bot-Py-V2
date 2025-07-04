"""Contains cog classes for SU platform access cookie authorisation check interactions."""

import logging
from enum import Enum
from typing import TYPE_CHECKING, override

import aiohttp
import bs4
import discord
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

__all__: "Sequence[str]" = (
    "CheckSUPlatformAuthorisationCommandCog",
    "CheckSUPlatformAuthorisationTaskCog",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

REQUEST_HEADERS: "Final[Mapping[str, str]]" = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

REQUEST_COOKIES: "Final[Mapping[str, str]]" = {
    ".ASPXAUTH": settings["SU_PLATFORM_ACCESS_COOKIE"]
}

PROFILE_URL: "Final[str]" = "https://guildofstudents.com/profile"
ORGANISATION_URL: "Final[str]" = "https://www.guildofstudents.com/organisation/admin"


class CheckSUPlatformAuthorisationBaseCog(TeXBotBaseCog):
    """Cog class that defines the base for token authorisation functions."""

    class TokenStatus(Enum):
        """
        Enum class that defines the status of the token.

        INVALID: The token does not have access to a user, meaning it is invalid or expired.
        VALID: The token is a valid user, but not neccessarily admin to an organisation.
        AUTHORISED: The token is a valid user and has access to an organisation.
        """

        INVALID = (
            logging.WARNING,
            "The auth session cookie is not associated with any MSL user, "
            "meaning it is invalid or expired.",
        )
        VALID = (
            logging.WARNING,
            "The auth session cookie is associated with a valid MSL user, "
            "but is not an admin to any MSL organisations.",
        )
        AUTHORISED = (
            logging.INFO,
            "The auth session cookie is associated with a valid MSL user and "
            "has access to at least one MSL organisation.",
        )

    async def _fetch_url_content_with_session(self, url: str) -> str:
        """Fetch the HTTP content at the given URL, using a shared aiohttp session."""
        async with (
            aiohttp.ClientSession(
                headers=REQUEST_HEADERS,
                cookies=REQUEST_COOKIES,
            ) as http_session,
            http_session.get(url) as http_response,
        ):
            return await http_response.text()

    async def get_token_status(self) -> TokenStatus:
        """
        Definition of method to get the status of the token.

        This is done by checking if the token is valid and if it is,
        checking if the token has access to the organisation.
        """
        response_object: bs4.BeautifulSoup = bs4.BeautifulSoup(
            await self._fetch_url_content_with_session(PROFILE_URL), "html.parser"
        )
        page_title: bs4.Tag | bs4.NavigableString | None = response_object.find("title")
        if not page_title or "Login" in str(page_title):
            logger.debug("Token is invalid or expired.")
            return self.TokenStatus.INVALID

        organisation_admin_url: str = f"{ORGANISATION_URL}/{settings['ORGANISATION_ID']}"
        response_html: str = await self._fetch_url_content_with_session(organisation_admin_url)

        if "admin tools" in response_html.lower():
            return self.TokenStatus.AUTHORISED

        if "You do not have any permissions for this organisation" in response_html.lower():
            return self.TokenStatus.VALID

        logger.warning("Unexpected response when checking token authorisation.")
        return self.TokenStatus.INVALID

    async def get_token_groups(self) -> "Iterable[str]":
        """
        Definition of method to get the groups the token has access to.

        This is done by requesting the user profile page and
        scraping the HTML for the list of groups.
        """
        response_object: bs4.BeautifulSoup = bs4.BeautifulSoup(
            await self._fetch_url_content_with_session(PROFILE_URL), "html.parser"
        )

        page_title: bs4.Tag | bs4.NavigableString | None = response_object.find("title")

        if not page_title:
            PROFILE_PAGE_INVALID: Final[str] = (
                "Profile page returned no content when checking token authorisation."
            )
            logger.warning(PROFILE_PAGE_INVALID)
            return ()

        if "Login" in str(page_title):
            EXPIRED_AUTH_MESSAGE: Final[str] = (
                "Authentication redirected to login page. Token is invalid or expired."
            )
            logger.warning(EXPIRED_AUTH_MESSAGE)
            return ()

        profile_section_html: bs4.Tag | bs4.NavigableString | None = response_object.find(
            "div",
            {"id": "profile_main"},
        )

        if profile_section_html is None:
            logger.warning(
                "Couldn't find the profile section of the user "
                "when scraping the website's HTML."
            )
            logger.debug("Retrieved HTML: %s", response_object.text)
            return ()

        user_name: bs4.Tag | bs4.NavigableString | int | None = profile_section_html.find("h1")

        if not isinstance(user_name, bs4.Tag):
            logger.warning("Found user profile but couldn't find their name.")
            logger.debug("Retrieved HTML: %s", response_object.text)
            return ()

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
            return ()

        organisations: Iterable[str] = [
            list_item.get_text(strip=True) for list_item in parsed_html.find_all("li")
        ]

        logger.debug(
            "Admin Token has admin access to: %s as user %s",
            organisations,
            user_name.text,
        )

        return organisations


class CheckSUPlatformAuthorisationCommandCog(CheckSUPlatformAuthorisationBaseCog):
    """Cog class that defines the "/check-su-platform-authorisation-cookie" command."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="check-su-platform-authorisation",
        description="Checks the authorisations held by the SU access token.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def check_su_platform_authorisation(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """
        Definition of the "check_su_platform_authorisation" command.

        The "check_su_platform_authorisation" command will retrieve the profile for the user.
        The profile page will contain the user's name and a list of the MSL organisations
        the user has administrative access to.
        """
        await ctx.defer(ephemeral=True)
        async with ctx.typing():
            await ctx.followup.send(
                content=(
                    f"SU Platform Access Cookie has access to the following MSL Organisations:"
                    f"\n{
                        ',\n'.join(
                            organisation for organisation in await self.get_token_groups()
                        )
                    }"
                ),
                ephemeral=True,
            )


class CheckSUPlatformAuthorisationTaskCog(CheckSUPlatformAuthorisationBaseCog):
    """Cog class that defines a repeated background task for checking SU Platform Access Cookie."""  # noqa: E501, W505

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

    @tasks.loop(**settings["AUTO_AUTH_SESSION_COOKIE_CHECKING_INTERVAL"])
    @capture_guild_does_not_exist_error
    async def token_authorisation_check_task(self) -> None:
        """
        Definition of the background task that checks the token authorisation.

        The task will check if the token is valid and if it is, it will retrieve the
        groups the token has access to.
        """
        logger.debug("Running token authorisation check task...")

        token_status: CheckSUPlatformAuthorisationBaseCog.TokenStatus = (
            await self.get_token_status()
        )

        match token_status:
            case self.TokenStatus.AUTHORISED:
                logger.info("Token is valid and has access to the organisation.")
                return

            case self.TokenStatus.VALID:
                logger.warning("Token is valid but does not have access to the organisation.")
                return

            case self.TokenStatus.INVALID:
                logger.warning("Token is invalid or expired.")
                return

    @token_authorisation_check_task.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
