"""Module for handling MSL related commands."""

import logging
from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog
from utils.msl import finance

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext


__all__: "Sequence[str]" = ("MSLCommandsCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class MSLCommandsCog(TeXBotBaseCog):
    """Cog for handling MSL related commands."""

    @discord.slash_command(name="get-expense", description="Command to fetch an expense.")
    @discord.option(
        name="expense_id",
        input_type=str,
        description="The ID of the expense to fetch.",
        required=True,
    )
    async def get_expense(self, ctx: "TeXBotApplicationContext", expense_id: str) -> None:
        """Fetch an MSL expense with the given ID."""
        if not expense_id.isdigit():
            await ctx.respond(
                "The expense ID must be a positive integer. Please try again with a valid ID.",
                ephemeral=True,
            )
            return

        await ctx.defer(ephemeral=True)

        expense = await finance.get_expense(int(expense_id))

        if not expense:
            await ctx.followup.send(
                f"Could not fetch expense with ID {expense_id}. "
                "Please ensure the ID is correct and try again.",
                ephemeral=True,
            )
            return

        await ctx.followup.send(
            str(expense),
            ephemeral=True,
        )
