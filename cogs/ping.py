"""Contains cog classes for any ping interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("PingCommandCog",)


import random

import discord

from config import settings
from utils import TeXBotApplicationContext, TeXBotBaseCog
from utils.msl import get_product_customisations


class PingCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/remindme" command and its call-back method."""

    @discord.slash_command(description="Replies with Pong!")  # type: ignore[no-untyped-call, misc]
    async def ping(self, ctx: TeXBotApplicationContext) -> None:
        """Definition & callback response of the "ping" command."""
        await ctx.respond(
            random.choices(
                [
                    "Pong!",
                    "`64 bytes from TeX-Bot: icmp_seq=1 ttl=63 time=0.01 ms`",
                ],
                weights=(
                    100 - settings["PING_COMMAND_EASTER_EGG_PROBABILITY"],
                    settings["PING_COMMAND_EASTER_EGG_PROBABILITY"],
                ),
            )[0],
            ephemeral=True,
        )





    # TODO: ONLY FOR TESTING REMOVE WHEN DONE

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="test-customisation-report",
        description="returns a customisation report",
    )
    async def test_customisation_report(self, ctx: TeXBotApplicationContext) -> None:
        initial_message: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            content="Generating customisation report...",
        )

        customisation_report: set[dict[str, str]] = await get_product_customisations(product_id="10211090")

        await initial_message.edit(
            content=f"Customisation report for product 10211090:\n\n{customisation_report}",
        )


