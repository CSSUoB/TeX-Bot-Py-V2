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

        In order to do this the bot will need to hold a role above that of the committee role.
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role
        main_guild: discord.Guild = self.bot.main_guild
        handover_channel: discord.TextChannel = await self.bot.handover_channel

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Running handover procedures... :hourglass:",
        )
        logger.debug("Running the handover command!")

        highest_role: discord.Role = main_guild.me.top_role
        if highest_role.position < committee_role.position:
            logger.debug(
                ":warning: This command requires the bot to hold a role higher than that of "
                "the committee role to perform this action. Aborting operation. :warning:",
            )
            await initial_response.edit(
                content="This command requires the bot to hold a role higher than that "
                "of the committee role to perform this action. Aborting operation.",
            )
            return

        for category in main_guild.categories:
            logger.debug("Found category: %s", category.name.lower())
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

        for member in committee_role.members:
            logger.debug("Giving user: %s, access to #handover", member)
            await handover_channel.set_permissions(
                member,
                read_messages=True,
                send_messages=True,
            )

            logger.debug("Removing committee role from user: %s", member)
            await member.remove_roles(
                committee_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"handover\"",
            )

        await initial_response.edit(
            content=":hourglass: Giving committee-elect committee role and "
            "removing committee-elect... :hourglass:",
        )

        for member in committee_elect_role.members:
            logger.debug("Giving user: %s, the committee role.", member)
            await member.add_roles(
                committee_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"handover\"",
            )

            logger.debug("Removing committee-elect role from user: %s", member)
            await member.remove_roles(
                committee_elect_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"handover\"",
            )

        await initial_response.edit(content=":white_check_mark: Handover procedure complete!")


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

        The "reset_roles" command removes the memeber and respective year roles from
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
        await initial_response.edit(
            content=":hourglass: Removed member role from all users...",
        )

        await GroupMadeMember._default_manager.all().adelete()

        await initial_response.edit(
            content=":white_check_mark: Deleted all members from the database...",
        )
        logger.debug("Deleted all members from the database.")

        year_role_names: list[str] = [
            "Foundation Year",
            "First Year",
            "Second Year",
            "Final Year",
            "Year In Industry",
            "Year Abroad",
            "PGT",
        ]
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
        await initial_response.edit(content=":white_check_mark: Role reset complete!")

