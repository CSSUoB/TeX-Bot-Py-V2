"""Module for handling society events in a Discord bot."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog
from utils.msl import fetch_guild_activities

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext


__all__: "Sequence[str]" = ("SocietyEventsSlashCommandsCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class SocietyEventsSlashCommandsCog(TeXBotBaseCog):
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
        await ctx.defer(ephemeral=True)
        activities: dict[str, str] = await fetch_guild_activities(
            from_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),  # noqa: DTZ007
            to_date=datetime.strptime("2026-01-01", "%Y-%m-%d"),  # noqa: DTZ007
        )

        await ctx.followup.send(
            content=str(activities),
            ephemeral=True,
        )
