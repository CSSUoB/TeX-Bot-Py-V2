"""Contains cog classes for SU platform access cookie authorisation check interactions."""

import logging
from enum import Enum
from typing import TYPE_CHECKING, override

import discord
from discord.ext import tasks

from config import settings
from utils import CommandChecks, TeXBotBaseCog
from utils.error_capture_decorators import (
    capture_guild_does_not_exist_error,
)
from utils.msl import get_su_platform_access_cookie_status, get_su_platform_organisations

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBot, TeXBotApplicationContext

__all__: "Sequence[str]" = (
    "CheckSUPlatformAuthorisationCommandCog",
    "CheckSUPlatformAuthorisationTaskCog",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class SUPlatformAccessCookieStatus(Enum):
    """Enum class defining the status of the SU Platform Access Cookie."""

    INVALID = (
        logging.WARNING,
        (
            "The SU platform access cookie is not associated with any MSL user, "
            "meaning it is invalid or expired."
        ),
    )
    VALID = (
        logging.WARNING,
        (
            "The SU platform access cookie is associated with a valid MSL user, "
            "but is not an admin to any MSL organisations."
        ),
    )
    AUTHORISED = (
        logging.INFO,
        (
            "The SU platform access cookie is associated with a valid MSL user and "
            "has access to at least one MSL organisation."
        ),
    )


class CheckSUPlatformAuthorisationCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/check-su-platform-authorisation" command."""

    @discord.slash_command(
        name="check-su-platform-authorisation",
        description="Checks the authorisation held by the SU platform access cookie.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def check_su_platform_authorisation(self, ctx: "TeXBotApplicationContext") -> None:
        """
        Definition of the "check_su_platform_authorisation" command.

        The "check_su_platform_authorisation" command will retrieve the profile for the user.
        The profile page will contain the user's name and a list of the MSL organisations
        the user has administrative access to.
        """
        await ctx.defer(ephemeral=True)

        async with ctx.typing():
            su_platform_access_cookie_organisations: AbstractSet[str] = set(
                await get_su_platform_organisations()
            )

            await ctx.followup.send(
                content=(
                    "No MSL organisations are available to the SU platform access cookie. "
                    "Please check the logs for errors."
                    if not su_platform_access_cookie_organisations
                    else (
                        f"SU Platform Access Cookie has access to the following "
                        "MSL Organisations:"
                        f"\n{
                            ',\n'.join(
                                organisation
                                for organisation in su_platform_access_cookie_organisations
                            )
                        }"
                    )
                ),
                ephemeral=True,
            )


class CheckSUPlatformAuthorisationTaskCog(TeXBotBaseCog):
    """Cog class defining a repeated task for checking SU platform access cookie."""

    @override
    def __init__(self, bot: "TeXBot") -> None:
        """Start all task managers when this cog is initialised."""
        if settings["AUTO_SU_PLATFORM_ACCESS_COOKIE_CHECKING"]:
            _ = self.su_platform_access_cookie_check_task.start()

        super().__init__(bot)

    @override
    def cog_unload(self) -> None:
        """
        Unload-hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.su_platform_access_cookie_check_task.cancel()

    @tasks.loop(**settings["AUTO_SU_PLATFORM_ACCESS_COOKIE_CHECKING_INTERVAL"])
    @capture_guild_does_not_exist_error
    async def su_platform_access_cookie_check_task(self) -> None:
        """
        Definition of the repeated background task that checks the SU platform access cookie.

        The task will check if the cookie is valid and if it is, it will retrieve the
        MSL organisations the cookie has access to.
        """
        logger.debug("Running SU platform access cookie check task...")

        su_platform_access_cookie_status: tuple[int, str] = (
            await get_su_platform_access_cookie_status()
        ).value

        logger.log(
            level=su_platform_access_cookie_status[0],
            msg=su_platform_access_cookie_status[1],
        )

    @su_platform_access_cookie_check_task.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
