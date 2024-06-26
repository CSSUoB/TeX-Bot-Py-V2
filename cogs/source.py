"""Contains cog classes for any source interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("SourceCommandCog",)


import discord

from utils import TeXBotApplicationContext, TeXBotBaseCog


class SourceCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/source" command and its call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        description="Displays information about the source code of this bot.",
    )
    async def source(self, ctx: TeXBotApplicationContext) -> None:
        """Definition & callback response of the "source" command."""
        await ctx.respond(
            (
                "TeX-Bot is an open-source project "
                "made specifically for the CSS Discord server!\n"
                "You can see and contribute to the source code at [CSSUoB/TeX-Bot-Py-V2](https://github.com/CSSUoB/TeX-Bot-Py-V2)."
            ),
            ephemeral=True,
        )
