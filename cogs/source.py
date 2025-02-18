"""Contains cog classes for any source interactions."""

from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("SourceCommandCog",)


class SourceCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/source" command and its call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        description="Displays information about the source code of TeX-Bot.",
    )
    async def source(self, ctx: "TeXBotApplicationContext") -> None:
        """Definition & callback response of the "source" command."""
        await ctx.respond(
            (
                f"{self.bot.user.mention if self.bot.user else '**`@TeX-Bot`**'} "
                "is an open-source project, "
                "originally made to help manage [the UoB CSS Discord server](https://cssbham.com/discord)!\n"
                "You can see and contribute to the source code at [CSSUoB/TeX-Bot-Py-V2](https://github.com/CSSUoB/TeX-Bot-Py-V2)."
            ),
            ephemeral=True,
        )
