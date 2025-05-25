"""Contains cog class for helpop commands."""

import logging
from typing import TYPE_CHECKING

import discord

from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("HelpopCommandCog",)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class HelpopCommandCog(TeXBotBaseCog):
    """Cog for helpop commands."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="helpop",
        description="Create a private channel with committee.",
    )
    @CommandChecks.check_interaction_user_in_main_guild
    async def helpop(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """Create a private channel with committee."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild

        if isinstance(ctx.user, discord.User):
            await self.command_send_error(
                ctx=ctx,
                message="This command can only be used in the main guild.",
            )
            return

        committee_external_category: discord.CategoryChannel | None = discord.utils.get(
            main_guild.categories,
            name="Committee - External",
        )

        if committee_external_category is None:
            await self.command_send_error(
                ctx=ctx,
                message="The required discord category could not be found.",
            )
            return

        new_channel: discord.TextChannel = await main_guild.create_text_channel(
            name=f"helpop-{ctx.author.name}",
            category=committee_external_category,
        )

        await new_channel.edit(sync_permissions=True)

        await new_channel.set_permissions(
            target=ctx.user,
            read_messages=True,
            send_messages=True,
            view_channel=True,
        )

        await new_channel.send(
            content=f"Hello {ctx.author.mention}, this is a private channel with the committee"
            " to discuss an issue or concern. Please use the `/close-helpop` command "
            "after the issue is resolved."
        )

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="close-helpop",
        description="Close the helpop channel.",
    )
    async def close_helpop(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """Close the helpop channel."""
        if (
            not isinstance(ctx.channel, discord.TextChannel)
            or "helpop" not in ctx.channel.name
        ):
            await self.command_send_error(
                ctx=ctx,
                message="This command can only be used in a helpop channel.",
            )
            return

        await ctx.channel.delete()
