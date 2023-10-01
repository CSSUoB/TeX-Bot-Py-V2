import random

import discord

from cogs._utils import TeXBotCog
from config import settings


class PingCommandCog(TeXBotCog):
    @discord.slash_command(description="Replies with Pong!")  # type: ignore[no-untyped-call, misc] # noqa: E501
    async def ping(self, ctx: discord.ApplicationContext) -> None:
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
