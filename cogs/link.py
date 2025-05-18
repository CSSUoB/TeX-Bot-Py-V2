"""Contains cog classes for any invite link display interactions."""

from typing import TYPE_CHECKING

import discord

from config import settings
from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("LinkCommandCog",)


class LinkCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/link" command and its call-back method."""

    @discord.slash_command(description="Display the invite link to this server.")  # type: ignore[no-untyped-call, misc]
    async def link(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """Definition & callback response of the "link" command."""
        await ctx.respond(
            (
                f"Invite your friends to the {self.bot.group_short_name} Discord server: "
                f"{settings['DISCORD_INVITE_URL']}"
            ),
            ephemeral=False,
        )
