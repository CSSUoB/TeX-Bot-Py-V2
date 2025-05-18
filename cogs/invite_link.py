"""Contains cog classes for any invite link display interactions."""

from typing import TYPE_CHECKING

import discord

from config import settings
from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("InviteLinkCommandCog",)


class InviteLinkCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/invite-link" command and its call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="invite-link", description="Display the invite link to this server."
    )
    async def invite_link(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """Definition & callback response of the "invite-link" command."""
        await ctx.respond(
            (
                f"Invite your friends to the {self.bot.group_short_name} Discord server: "
                f"{settings['DISCORD_INVITE_URL']}"
            ),
            ephemeral=False,
        )
