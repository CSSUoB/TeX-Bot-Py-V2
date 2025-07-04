"""Contains cog classes for any write_roles interactions."""

from typing import TYPE_CHECKING

import discord

from config import settings
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("WriteRolesCommandCog",)


class WriteRolesCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/write-roles" command and its call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="write-roles", description="Populates #roles with the correct messages."
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def write_roles(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """
        Definition & callback response of the "write_roles" command.

        The "write_roles" command populates the "#roles" channel with the correct messages
        defined in the messages.json file.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        roles_channel: discord.TextChannel = await self.bot.roles_channel

        roles_message: str
        for roles_message in settings["ROLES_MESSAGES"]:
            await roles_channel.send(
                roles_message.replace("<Group_Name>", self.bot.group_short_name)
            )

        await ctx.respond("All messages sent successfully.", ephemeral=True)
