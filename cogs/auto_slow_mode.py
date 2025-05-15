"""Module to handle automatic slow mode for Discord channels."""

import logging
from typing import TYPE_CHECKING

import discord

from utils import TeXBotApplicationContext, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = ()

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class AutomaticSlowModeBaseCog(TeXBotBaseCog):
    """Base class for automatic slow mode functionality."""

    async def calculate_message_rate(ctx: TeXBotApplicationContext, channel: discord.Channel) -> None:
        """Calculate the message rate for a given channel."""
        raise NotImplementedError


class AutomaticSlowModeCog(AutomaticSlowModeBaseCog):
    """Cog to handle automatic slow mode for Discord channels."""

    @discord.slash_command(
        name="auto_slow_mode",
        description="Enable or disable automatic slow mode for a channel.",
    )
    async def auto_slow_mode(
        self,
        ctx: TeXBotApplicationContext,
        channel: discord.TextChannel = None,
    ) -> None:
        """Enable or disable automatic slow mode for a channel."""
        raise NotImplementedError
