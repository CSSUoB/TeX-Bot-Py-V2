"""Module to handle automatic slow mode for Discord channels."""

import logging
from typing import TYPE_CHECKING

import discord

from config import settings
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext


__all__: "Sequence[str]" = ("AutomaticSlowModeCommandCog",)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class AutomaticSlowModeBaseCog(TeXBotBaseCog):
    """Base class for automatic slow mode functionality."""

    async def calculate_message_rate(
        self, ctx: "TeXBotApplicationContext", channel: discord.TextChannel
    ) -> None:
        """Calculate the message rate for a given channel."""
        raise NotImplementedError


class AutomaticSlowModeCommandCog(AutomaticSlowModeBaseCog):
    """Cog to handle automatic slow mode for Discord channels."""

    @discord.slash_command(  # type: ignore[misc, no-untyped-call]
        name="toggle-auto-slow-mode",
        description="Enable or disable automatic slow mode.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def toggle_auto_slow_mode(  # type: ignore[misc, no-untyped-call]
        self,
        ctx: "TeXBotApplicationContext",
    ) -> None:
        """Enable or disable automatic slow mode for a channel."""
        # NOTE: This should be replaced when the settings are refactored in the draft PR.
        if settings["AUTO_SLOW_MODE"]:
            settings["AUTO_SLOW_MODE"] = False
            await ctx.send("Automatic slow mode is now disabled.")
            return

        settings["AUTO_SLOW_MODE"] = True
        await ctx.send("Automatic slow mode is now enabled.")
