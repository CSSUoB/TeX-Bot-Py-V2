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
        discord_invite_url: str | None = settings["DISCORD_INVITE_URL"]

        if not discord_invite_url:
            invite_destination_channel: discord.TextChannel | None = discord.utils.get(
                ctx.bot.main_guild.text_channels, name="welcome"
            )

            if invite_destination_channel is None:
                invite_destination_channel = await ctx.bot.rules_channel

            discord_invite_url = (
                await invite_destination_channel.create_invite(
                    reason=f'{ctx.user} used TeX Bot slash-command: "/invite-link"',
                    max_age=21600,
                )
            ).url

        await ctx.respond(
            (
                f"Invite your friends to the {self.bot.group_short_name} Discord server: "
                f"{discord_invite_url}"
            ),
            ephemeral=False,
        )
