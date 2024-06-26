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
    """Cog class that defines the handover command."""

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
        - Remove permissions for @Committee-Elect from all channels except #handover
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role
        main_guild: discord.Guild = self.bot.main_guild
        handover_channel: discord.TextChannel = await self.bot.handover_channel

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Running the handover procedures... :hourglass:",
        )
        logger.debug("Running the handover command!")

        for channel in main_guild.channels:
            if channel is handover_channel:
                continue
            await channel.set_permissions(committee_elect_role, overwrite=None)

        for member in committee_role.members:
            await handover_channel.set_permissions(
                member,
                read_messages=True,
                send_messages=True,
            )

            await member.remove_roles(
                committee_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"handover\"",
            )

        for member in committee_elect_role.members:
            await member.add_roles(
                committee_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"handover\"",
            )

            await member.remove_roles(
                committee_elect_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"handover\"",
            )

        initial_response.edit(content=":white_check_mark: Handover procedure complete!")


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

        The "reset_roles" command removes the mmeber and respective year roles from
        anyone that has them and subsequently resets the GroupMadeMember database Model.
        """
        member_role: discord.Role = await self.bot.member_role
        main_guild: discord.Guild = self.bot.main_guild

        logger.debug("Reset roles command called.")
        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Resetting membership and year roles... :hourglass:",
        )

        for member in member_role.members:
            await member.remove_roles(
                member_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"/reset_roles\"",
            )

        logger.debug("Removed member role from all users!")
        initial_response.edit(content=":hourglass: Removed member role from all users...")

        await GroupMadeMember._default_manager.all().adelete()

        initial_response.edit(
            content=":white_check_mark: Deleted all members from the database...",
        )
        logger.debug("Deleted all members from the database.")

        year_role_names: list[str] = ["Foundation Year", "First Year", "Second Year", "Final Year", "Year In Industry", "Year Abroad"]  # noqa: E501
        year_roles: list[discord.Role] = []

        for role_name in year_role_names:
            role: discord.Role | None = discord.utils.get(main_guild.roles, name=role_name)
            if isinstance(role, discord.Role):
                year_roles.append(role)

        for role in year_roles:
            for member in role.members:
                await member.remove_roles(
                    role,
                    reason=f"{ctx.user} used TeX Bot slash-command: \"reset_roles\"",
                )

        logger.debug("Execution of reset roles command complete!")
        initial_response.edit(content=":white_check_mark: Role reset complete!")

