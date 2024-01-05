"""Contains cog classes for any kick_no_introduction_discord_members interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("KickNoIntroductionDiscordMembersTaskCog",)

import functools
import logging
from logging import Logger
from typing import TYPE_CHECKING

import discord
from discord.ext import tasks

from config import settings
from exceptions import GuestRoleDoesNotExist
from utils import TeXBot, TeXBotBaseCog
from utils.error_capture_decorators import (
    ErrorCaptureDecorators,
    capture_guild_does_not_exist_error,
)

if TYPE_CHECKING:
    import datetime

logger: Logger = logging.getLogger("texbot")


class KickNoIntroductionDiscordMembersTaskCog(TeXBotBaseCog):
    """Cog class that defines the kick_no_introduction_discord_members task."""

    def __init__(self, bot: TeXBot) -> None:
        """Start all task managers when this cog is initialised."""
        if settings["SEND_GET_ROLES_REMINDERS"]:
            self.kick_no_introduction_discord_members.start()

        super().__init__(bot)

    def cog_unload(self) -> None:
        """
        Unload hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.kick_no_introduction_discord_members.cancel()

    @tasks.loop(hours=24)
    @functools.partial(
        ErrorCaptureDecorators.capture_error_and_close,
        error_type=GuestRoleDoesNotExist,
        close_func=ErrorCaptureDecorators.critical_error_close_func
    )
    @capture_guild_does_not_exist_error
    async def kick_no_introduction_discord_members(self) -> None:
        """
        Recurring task to kick any Discord members that have not introduced themselves.

        Other prerequisites must be met for this task to be activated, see README.md for the
        full list of conditions.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        guild: discord.Guild = self.bot.main_guild
        guest_role: discord.Role = await self.bot.guest_role

        member: discord.Member
        for member in guild.members:
            if guest_role in member.roles or member.bot:
                continue

            if not member.joined_at:
                logger.error(
                    (
                        "Member with ID: %s could not be checked whether to kick, "
                        "because their %s attribute was None."
                    ),
                    member.id,
                    repr("joined_at")
                )
                continue

            kick_no_introduction_discord_members_delay: datetime.timedelta = settings[
                "KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY"
            ]
            time_since_joining: datetime.timedelta = discord.utils.utcnow() - member.joined_at

            if time_since_joining > kick_no_introduction_discord_members_delay:
                try:
                    await member.kick(
                        reason=(
                            "Member was in server without introduction sent "
                            f"for longer than {kick_no_introduction_discord_members_delay}"
                        )
                    )
                except discord.Forbidden as kick_error:
                    logger.error(
                        "Member with ID: %s could not be kicked due to %s",
                        member.id,
                        kick_error.text
                    )

    @kick_no_introduction_discord_members.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
