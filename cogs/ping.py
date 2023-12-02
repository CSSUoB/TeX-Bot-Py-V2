"""Contains cog classes for any ping interactions."""

import random

import discord

from config import settings
from utils import TeXBotApplicationContext, TeXBotBaseCog


class PingCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/remindme" command and its call-back method."""

    @discord.slash_command(description="Replies with Pong!")  # type: ignore[no-untyped-call, misc]
    async def ping(self, ctx: TeXBotApplicationContext) -> None:
        """Definition & callback response of the "ping" command."""
        await ctx.respond(
            random.choices(
                [
                    "Pong!",
                    "64 bytes from TeX: icmp_seq=1 ttl=63 time=0.01 ms"
                ],
                weights=(
                    100 - settings["PING_COMMAND_EASTER_EGG_PROBABILITY"],
                    settings["PING_COMMAND_EASTER_EGG_PROBABILITY"]
                )
            )[0],
            ephemeral=True
        )
