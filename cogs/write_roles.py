"""Contains cog classes for any write_roles interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("WriteRolesCommandCog",)

import discord

from config import settings
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog


class WriteRolesCommandCog(TeXBotBaseCog):
    # noinspection SpellCheckingInspection
    """Cog class that defines the "/writeroles" command and its call-back method."""

    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="writeroles",
        description="Populates #roles with the correct messages."
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def write_roles(self, ctx: TeXBotApplicationContext) -> None:
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
                roles_message.replace("<Group_Name>", self.bot.group_name)
            )

        await ctx.respond("All messages sent successfully.", ephemeral=True)
