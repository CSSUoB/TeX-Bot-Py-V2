"""Contains cog classes for handover functionality."""


from collections.abc import Sequence

__all__: Sequence[str] = ("HandoverCommandCog", "ResetRolesCommandCog")

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

        To do this TeX-Bot will need to hold a role above that of the committee role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role

        handover_channel: AllChannelTypes | None = discord.utils.get(
            main_guild.channels,
            name="Handover",
        )

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
                content=":warning: This command requires the bot to hold a role higher than "
                "that of the committee role to perform this action. Operation aborted. "
                ":warning:",
            )
            return

        category: discord.CategoryChannel
        for category in main_guild.categories:
            if "committee" in category.name.lower() and "archive" not in category.name.lower():
                await initial_response.edit(
                    content=f":hourglass: Updating channels in category: {category.name} "
                    ":hourglass:",
                )
                for channel in category.channels:
                    logger.debug("Resetting channel permissions for channel: %s", channel)
                    await channel.set_permissions(committee_elect_role, overwrite=None)

        await initial_response.edit(
            content=":hourglass: Giving committee members access to #handover and "
            "removing committee role... :hourglass:",
        )

        committee_member: discord.Member
        for committee_member in committee_role.members:

            if isinstance(handover_channel, discord.TextChannel):
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
            content=":hourglass: Giving committee-elect Committee role and "
            "removing committee-elect... :hourglass:",
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


class ResetRolesCommandCog(TeXBotBaseCog):
    """Cog class that defines the reset_roles command."""

    YEAR_ROLE_NAMES: Final[frozenset[str]] = frozenset(
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
        name="reset_roles",
        description="Removes member and year roles from all users",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def reset_roles(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "reset_roles" command.

        The "reset_roles" command removes the "Memeber" and respective year roles from
        any user that has them and subsequently resets the GroupMadeMember database model.
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
            content=":hourglass: Removed member role from all users...",
        )

        await GroupMadeMember._default_manager.all().adelete()

        await initial_response.edit(
            content=":white_check_mark: Deleted all members from the database...",
        )
        logger.debug("Deleted all members from the database.")

        year_roles: set[discord.Role] = {
            role
            for role_name
            in self.YEAR_ROLE_NAMES
            if isinstance(
                (role := discord.utils.get(main_guild.roles, name=role_name)), discord.Role,
            )
        }

        for role in year_roles:
            for member in role.members:
                await member.remove_roles(
                    role,
                    reason=f"{ctx.user} used TeX-Bot slash-command: \"reset_roles\"",
                )

        logger.debug("Execution of reset roles command complete!")
        await initial_response.edit(content=":white_check_mark: Role reset complete!")
