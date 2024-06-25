"""Contains cog classes for handover functionality."""


from collections.abc import Sequence

__all__: Sequence[str] = ("HandoverCommandCog", "ResetRolesCommandCog")

import logging
from logging import Logger

import discord

from db.core.models import GroupMadeMember
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")


class HandoverCommandCog(TeXBotBaseCog):
    """Cog class thaat defines the handover command."""

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="handover",
        description="Initiates the discord handover procedure for new committee",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def handover(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "handover" command.

        The "handover" command runs the relavent handover methods
        which will perform the following actions:
        - Give @Committee role to anyone with @Committee-Elect
        - Remove @Committee-Elect from anyone that has it
        - Remove permissions for @Committee-Elect from all channels except #Handover
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role
        main_guild: discord.Guild = self.bot.main_guild

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            "Running handover procedures!!",
        )
        logger.debug("Running the handover command!")

        for member in main_guild.members:
            if committee_elect_role in member.roles:
                await member.add_roles(committee_role, reason="")


        initial_response.edit(content="Done!!")


class ResetRolesCommandCog(TeXBotBaseCog):
    """Cog class that defines the reset_roles command."""

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="reset_roles",
        description="Resets member and year roles",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def reset_roles(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "reset_roles" command.

        The "reset_roles" command removes the mmeber role from anyone that has it
        and subsequently calls the method to reset the membership database.
        """
        member_role: discord.Role = await self.bot.member_role
        main_guild: discord.Guild = self.bot.main_guild

        logger.debug("Reset roles command called.")
        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            "Running reset roles!!",
        )

        for member in main_guild.members:
            if member_role in member.roles:
                await member.remove_roles(
                    member_role,
                    reason=f"{ctx.user} used TeX Bot slash-command: \"/reset_roles\"",
                )

        logger.debug("Removed member role from all users!")
        initial_response.edit(content="Removed member role from all users!")

        await GroupMadeMember._default_manager.all().adelete()

        initial_response.edit(content="Deleted all members from the database!")
        logger.debug("Deleted all members from the database.")

        logger.debug("Execution of reset roles command complete!")
        initial_response.edit(content="Complete!")

