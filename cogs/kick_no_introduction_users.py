"""Contains cog classes for any kick_no_introduction_users interactions."""

import functools
import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import tasks

from cogs._utils import ErrorCaptureDecorators, TeXBotCog, capture_guild_does_not_exist_error
from config import settings
from exceptions import GuestRoleDoesNotExist
from utils import TeXBot

if TYPE_CHECKING:
    import datetime


class KickNoIntroductionUsersTaskCog(TeXBotCog):
    """Cog class that defines the kick_no_introduction_users task."""

    def __init__(self, bot: TeXBot) -> None:
        """Start all task managers when this cog is initialised."""
        if settings["SEND_GET_ROLES_REMINDERS"]:
            self.kick_no_introduction_users.start()

        super().__init__(bot)

    def cog_unload(self) -> None:
        """
        Unload hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.kick_no_introduction_users.cancel()

    @tasks.loop(hours=24)
    @functools.partial(
        ErrorCaptureDecorators.capture_error_and_close,
        error_type=GuestRoleDoesNotExist,
        close_func=ErrorCaptureDecorators.critical_error_close_func
    )
    @capture_guild_does_not_exist_error
    async def kick_no_introduction_users(self) -> None:
        """
        Recurring task to kick any Discord users that have not introduced themselves.

        Other prerequisites must be met for this task to be activated, see README.md for the
        full list of conditions.
        """
        guild: discord.Guild = self.bot.css_guild
        guest_role: discord.Role = await self.bot.guest_role

        member: discord.Member
        for member in guild.members:
            if guest_role in member.roles or member.bot:
                continue

            if not member.joined_at:
                logging.error(
                    (
                        "Member with ID: %s could not be checked whether to kick,"
                        " because their \"joined_at\" attribute was None."
                    ),
                    member.id
                )
                continue

            kick_no_introduction_members_delay: datetime.timedelta = settings[
                "KICK_NO_INTRODUCTION_MEMBERS_DELAY"
            ]
            time_since_joining: datetime.timedelta = discord.utils.utcnow() - member.joined_at

            if time_since_joining > kick_no_introduction_members_delay:
                try:
                    await member.kick(
                        reason=(
                            "Member was in server without introduction sent"
                            f" for longer than {kick_no_introduction_members_delay}"
                        )
                    )
                except discord.Forbidden as kick_error:
                    logging.error(
                        "Member with ID: %s could not be kicked due to %s",
                        member.id,
                        kick_error.text
                    )

    @kick_no_introduction_users.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
