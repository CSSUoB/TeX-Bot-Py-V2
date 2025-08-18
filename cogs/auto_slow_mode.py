"""Module to handle automatic slow mode for Discord channels."""

import logging
from typing import TYPE_CHECKING, override

import discord
from discord.ext import tasks

from config import settings
from utils import CommandChecks, TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBot, TeXBotApplicationContext


__all__: "Sequence[str]" = ("AutomaticSlowModeCommandCog", "AutomaticSlowModeTaskCog")


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class AutomaticSlowModeBaseCog(TeXBotBaseCog):
    """Base class for automatic slow mode functionality."""

    async def calculate_message_rate(self, channel: discord.TextChannel) -> int:
        """
        Calculate the message rate for a given channel.

        Returns the number of messages per minute, rounded to the nearest integer.
        This is based on the previous 5 minutes of messages.
        """
        from datetime import UTC, datetime, timedelta

        # TODO: Make the time period user configurable.  # noqa: FIX002

        count = len(
            [
                message
                async for message in channel.history(
                    after=datetime.now(UTC) - timedelta(minutes=5),
                    oldest_first=False,
                    limit=None,
                )
            ]
        )

        logger.debug(
            "Channel: %s | Message count in last 5 minutes: %d | Rate: %d",
            channel.name,
            count,
            round(count / 5),
        )

        return round(count / 5)


class AutomaticSlowModeTaskCog(AutomaticSlowModeBaseCog):
    """Task to handle automatic slow mode for Discord channels."""

    @override
    def __init__(self, bot: "TeXBot") -> None:
        """Start all task managers when this cog is initialised."""
        if settings["AUTO_SLOW_MODE"]:
            _ = self.auto_slow_mode_task.start()

        super().__init__(bot)

    @override
    def cog_unload(self) -> None:
        """
        Unload-hook that ends all running tasks whenever the cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.auto_slow_mode_task.cancel()

    @tasks.loop(seconds=60)
    @capture_guild_does_not_exist_error
    async def auto_slow_mode_task(self) -> None:
        """Task to automatically adjust slow mode in channels."""
        import time

        time.process_time()
        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                message_rate: int = await self.calculate_message_rate(channel)
                if message_rate > 5:
                    await channel.edit(
                        slowmode_delay=10, reason="TeX-Bot auto slow mode enabled."
                    )
                await channel.edit(slowmode_delay=0, reason="TeX-Bot auto slow mode disabled.")
        logger.debug("Time taken to calculate message rate: %s seconds", time.process_time())

    @auto_slow_mode_task.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()


class AutomaticSlowModeCommandCog(AutomaticSlowModeBaseCog):
    """Cog to handle automatic slow mode for Discord channels."""

    @discord.slash_command(  # type: ignore[misc, no-untyped-call]
        name="toggle-auto-slow-mode",
        description="Enable or disable automatic slow mode.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def toggle_auto_slow_mode(  # type: ignore[misc]
        self,
        ctx: "TeXBotApplicationContext",
    ) -> None:
        """Enable or disable automatic slow mode for a channel."""
        # NOTE: This should be replaced when the settings improved in PR #221
        if settings["AUTO_SLOW_MODE"]:
            settings["AUTO_SLOW_MODE"] = False
            await ctx.respond(
                "Automatic slow mode is now disabled."
                "If you would like to keep it disabled, please remember to "
                "update the deployment variables as well. "
                "If you do not, it will be re-enabled when the bot restarts.",
            )
            return

        settings["AUTO_SLOW_MODE"] = True
        await ctx.respond(
            "Automatic slow mode is now enabled."
            "If you would like to keep it enabled, please remember to "
            "update the deployment variables as well. "
            "If you do not, it will be disabled again when the bot restarts.",
        )
