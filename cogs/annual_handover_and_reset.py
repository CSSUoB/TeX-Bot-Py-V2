"""Contains cog classes for annual handover and role reset functionality."""


from collections.abc import Sequence

__all__: Sequence[str] = ("HandoverCommandCog", "AnnualResetRolesCommandCog")

import logging
from logging import Logger
from typing import Final

import discord

from db.core.models import GroupMadeMember
from utils import AllChannelTypes, CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")


class HandoverCommandCog(TeXBotBaseCog):
    """Cog class that defines the handover command."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="handover",
        description="Initiates the annual Discord handover procedure for new committee",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def handover(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "handover" command.

        The "handover" command runs the relevant handover methods
        which will perform the following actions:
        - Give the "Committee" role to any users that have the "Committee-Elect" role
        - Remove the "Committee-Elect" role from any user that has it
        - Remove the permissions for the "Committee-Elect" role
          from all channels except "#handover"

        To do this, TeX-Bot will need to hold a role above that of the committee role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Running handover procedures... :hourglass:",
        )
        logger.debug("Running the handover command!")

        if main_guild.me.top_role.position < committee_role.position:
            logger.debug(
                "Handover command aborted because the bot did not "
                "hold a role above the committee role.",
            )
            await initial_response.edit(
                content=(
                    ":warning: This command requires TeX-Bot to hold a role higher than "
                    "that of the \"Committee\" role to perform this action. Operation aborted."
                    " :warning:"
                ),
            )
            return

        category: discord.CategoryChannel
        for category in main_guild.categories:
            if "committee" not in category.name.lower() or "archive" in category.name.lower():
                continue

            await initial_response.edit(
                content=f":hourglass: Updating channels in category: {category.name} "
                ":hourglass:",
            )
            channel: AllChannelTypes
            for channel in category.channels:
                logger.debug("Resetting channel permissions for channel: %s", channel)
                await channel.set_permissions(committee_elect_role, overwrite=None)

        await initial_response.edit(
            content=(
                ":hourglass: Giving committee users access to the #handover channel and "
                "removing the \"Committee\" role... :hourglass:"
            ),
        )

        handover_channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            name="Handover",
        )

        committee_member: discord.Member
        for committee_member in committee_role.members:
            if handover_channel:
                logger.debug("Giving user: %s, access to #handover", committee_member)
                await handover_channel.set_permissions(
                    committee_member,
                    read_messages=True,
                    send_messages=True,
                )

            logger.debug("Removing Committee role from user: %s", committee_member)
            await committee_member.remove_roles(
                committee_role,
                reason=f"{ctx.user} used TeX-Bot slash-command: \"handover\"",
            )

        await initial_response.edit(
            content=":hourglass: Giving committee-elect users the \"Committee\" role "
            "and removing their \"Committee-Elect\" role... :hourglass:",
        )

        committee_elect_member: discord.Member
        for committee_elect_member in committee_elect_role.members:
            logger.debug("Giving user: %s, the committee role.", committee_elect_member)
            await committee_elect_member.add_roles(
                committee_role,
                reason=f"{ctx.user} used TeX-Bot slash-command: \"handover\"",
            )

            logger.debug("Removing Committee-Elect role from user: %s", committee_elect_member)
            await committee_elect_member.remove_roles(
                committee_elect_role,
                reason=f"{ctx.user} used TeX-Bot slash-command: \"handover\"",
            )

        await initial_response.edit(content=":white_check_mark: Handover procedure complete!")


class AnnualResetRolesCommandCog(TeXBotBaseCog):
    """Cog class that defines the reset_roles command."""

    ACADEMIC_YEAR_ROLE_NAMES: Final[frozenset[str]] = frozenset(
        {
            "Foundation Year",
            "First Year",
            "Second Year",
            "Final Year",
            "Year In Industry",
            "Year Abroad",
            "PGT",
        },
    )

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="annual_role_reset",
        description="Removes the @Member role and academic year roles from all users",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def annual_role_reset(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "reset_roles" command.

        The "reset_roles" command removes the "Member" and academic year roles
        from any user that has them and subsequently deletes all instances of
        the GroupMadeMember database model.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        member_role: discord.Role = await self.bot.member_role

        logger.debug("Reset roles command called.")
        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Resetting membership and year roles... :hourglass:",
        )

        member: discord.Member
        for member in member_role.members:
            await member.remove_roles(
                member_role,
                reason=f"{ctx.user} used TeX-Bot slash-command: \"/reset_roles\"",
            )

        logger.debug("Removed Member role from all users!")
        await initial_response.edit(
            content=":hourglass: Removed Member role from all users...",
        )

        await GroupMadeMember._default_manager.all().adelete()

        await initial_response.edit(
            content=":white_check_mark: Deleted all members from the database...",
        )
        logger.debug("Deleted all members from the database.")

        year_roles: set[discord.Role] = {
            role
            for role_name
            in self.ACADEMIC_YEAR_ROLE_NAMES
            if isinstance(
                (role := discord.utils.get(main_guild.roles, name=role_name)),
                discord.Role,
            )
        }

        year_role: discord.Role
        for year_role in year_roles:
            logger.debug("Removing all members from role: %s", year_role)
            year_role_member: discord.Member
            for year_role_member in year_role.members:
                await year_role_member.remove_roles(
                    year_role,
                    reason=f"{ctx.user} used TeX-Bot slash-command: \"reset_roles\"",
                )

        logger.debug("Execution of reset roles command complete!")
        await initial_response.edit(content=":white_check_mark: Role reset complete!")
