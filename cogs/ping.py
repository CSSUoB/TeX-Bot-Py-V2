"""Contains cog classes for any ping interactions."""

import random
from typing import TYPE_CHECKING

import discord

from config import settings
from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("PingCommandCog",)


class PingCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/ping" command and its call-back method."""

    @discord.slash_command(name="ping", description="Replies with Pong!")
    async def ping(self, ctx: "TeXBotApplicationContext") -> None:
        """Definition & callback response of the "ping" command."""
        await ctx.respond(
            random.choices(  # noqa: S311
                ["Pong!", "`64 bytes from TeX-Bot: icmp_seq=1 ttl=63 time=0.01 ms`"],
                # NOTE: The probability is held as a fraction between 0 & 1, so the
                # weight of the common response is the remainder of that same scale.
                weights=(
                    1 - settings.commands.ping.easter_egg_probability,
                    settings.commands.ping.easter_egg_probability,
                ),
            )[0],
            ephemeral=True,
        )
