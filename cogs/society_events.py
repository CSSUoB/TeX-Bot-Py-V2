"""Module for handling society events in a Discord bot."""

import logging
from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog
from utils.msl import fetch_guild_activities

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext


__all__: "Sequence[str]" = ("SocietyEventsSlashCommands",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class SocietyEventsSlashCommands(TeXBotBaseCog):
    """Cog Class for handling society event commands."""

    society_events: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="society-events",
        description="Commands for managing society events.",
    )

    @society_events.command(
        name="list-all",
        desciption="List all society events.",
    )
    async def list_all_events(self, ctx: "TeXBotApplicationContext") -> None:
        """List all society events."""
        activities: dict[str, str] = await fetch_guild_activities()

        await ctx.respond(
            content=activities,
            ephemeral=True,
        )
