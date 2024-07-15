"""Contains cog classes for annual handover and role reset functionality."""


from collections.abc import Sequence

__all__: Sequence[str] = (
    "CommitteeHandoverCommandCog",
    "AnnualRolesResetCommandCog",
    "AnnualYearChannelsIncrementCommandCog",
)

import datetime
import logging
from logging import Logger
from typing import Final

import discord

from db.core.models import GroupMadeMember
from utils import AllChannelTypes, CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")


class CommitteeHandoverCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/committee-handover" command."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="committee-handover",
        description="Initiates the annual Discord handover procedure for new committee",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def committee_handover(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "committee_handover" command.

        The "committee_handover" command runs the relevant handover methods
        which will perform the following actions:
        - Give the "Committee" role to any users that have the "Committee-Elect" role
        - Remove the "Committee-Elect" role from any user that has it
        - Remove the permissions for the "Committee-Elect" role
          from all channels except "#handover"

        To do this, TeX-Bot will need to hold a role above that of the "Committee" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            content=":hourglass: Running handover procedures... :hourglass:",
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
                content=(
                    f":hourglass: Updating channels in category: {category.name} "
                    ":hourglass:"
                ),
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

        automod_role: discord.Role | None = discord.utils.get(main_guild.roles, name="Automod")

        committee_member: discord.Member
        for committee_member in committee_role.members:
            if committee_member.bot:
                continue

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
                reason=f"{ctx.user} used TeX-Bot slash-command: \"committee-handover\"",
            )

            if automod_role and automod_role in committee_member.roles:
                await committee_member.remove_roles(
                    automod_role,
                    reason=f"{ctx.user} used TeX-Bot slash-command: \"committee-handover\"",
                )

        await initial_response.edit(
            content=(
                ":hourglass: Giving committee-elect users the \"Committee\" role "
                "and removing their \"Committee-Elect\" role... :hourglass:"
            ),
        )

        committee_elect_member: discord.Member
        for committee_elect_member in committee_elect_role.members:
            if committee_elect_member.bot:
                continue
            logger.debug("Giving user: %s, the committee role.", committee_elect_member)
            await committee_elect_member.add_roles(
                committee_role,
                reason=f"{ctx.user} used TeX-Bot slash-command: \"committee-handover\"",
            )

            logger.debug("Removing Committee-Elect role from user: %s", committee_elect_member)
            await committee_elect_member.remove_roles(
                committee_elect_role,
                reason=f"{ctx.user} used TeX-Bot slash-command: \"committee-handover\"",
            )

        await initial_response.edit(content=":white_check_mark: Handover procedure complete!")


class AnnualRolesResetCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/annual-roles-reset" command."""

    ACADEMIC_YEAR_ROLE_NAMES: Final[frozenset[str]] = frozenset(
        {
            "Foundation Year",
            "First Year",
            "Second Year",
            "Final Year",
            "Year In Industry",
            "Year Abroad",
            "PGT",
            "Student Rep",
        },
    )

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="annual-roles-reset",
        description="Removes the @Member role and academic year roles from all users",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def annual_roles_reset(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "annual_roles_reset" command.

        The "annual_roles_reset" command removes the "Member" and academic year roles
        from any user that has them and subsequently deletes all instances of
        the GroupMadeMember database model.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        member_role: discord.Role = await self.bot.member_role

        logger.debug("Reset roles command called.")
        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            content=":hourglass: Resetting membership and year roles... :hourglass:",
        )

        member: discord.Member
        for member in member_role.members:
            await member.remove_roles(
                member_role,
                reason=f"{ctx.user} used TeX-Bot slash-command: \"/annual_roles_reset\"",
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
            if (role := discord.utils.get(main_guild.roles, name=role_name))
        }

        year_role: discord.Role
        for year_role in year_roles:
            logger.debug("Removing all members from role: %s", year_role)
            year_role_member: discord.Member
            for year_role_member in year_role.members:
                await year_role_member.remove_roles(
                    year_role,
                    reason=f"{ctx.user} used TeX-Bot slash-command: \"annual_roles_reset\"",
                )

        logger.debug("Execution of reset roles command complete!")
        await initial_response.edit(content=":white_check_mark: Role reset complete!")

class AnnualYearChannelsIncrementCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/increment-year-channels" command."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="increment-year-channels",
        description="Iterates the year channels, archiving and creating channels as needed.",
    )
    async def increment_year_channels(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition and callback response of the "increment_year_channels" command.

        The increment_year_channels command:
        - Archives the current final-years channel
        - Renames the current second year channel to final-years
        - Renames the current first year channel to second-years
        - Creates a new first years channel
        """
        main_guild: discord.Guild = self.bot.main_guild
        guest_role: discord.Role = await self.bot.guest_role

        initial_message: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            content=":hourglass: Processing year channel iteration... :hourglass:",
        )

        final_year_channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            name="final-years",
        )

        if final_year_channel:
            await initial_message.edit(
                content=":hourglass: Archiving final year channel... :hourglass:",
            )
            archivist_role: discord.Role = await self.bot.archivist_role

            await final_year_channel.set_permissions(guest_role, overwrite=None)
            await final_year_channel.set_permissions(archivist_role, read_messages=True)

            await final_year_channel.edit(
                name="final-years-" + str(datetime.datetime.now(tz=datetime.UTC).year),
            )

            archived_category: discord.CategoryChannel | None = discord.utils.get(
                main_guild.categories,
                name="Archived",
            )

            if archived_category:
                await final_year_channel.edit(
                    category=archived_category,
                    sync_permissions=True,
                )

        second_year_channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            name="second-years",
        )

        if second_year_channel:
            await second_year_channel.edit(name="final-years")

        first_year_channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            name="first-years",
        )

        if first_year_channel:
            await first_year_channel.edit(name="second-years")

        year_channels_category: discord.CategoryChannel | None = discord.utils.get(
            main_guild.categories,
            name="Year Chats",
        )

        await initial_message.edit(content=(
            ":hourglass: Creating new first year channel and setting permissions... "
            ":hourglass:"
        ))

        new_first_year_channel: discord.TextChannel = await main_guild.create_text_channel(
            name="first-years",
        )

        if year_channels_category:
            await new_first_year_channel.edit(
                category=year_channels_category,
                sync_permissions=True,
                position=0,
            )

            await initial_message.edit(
                content=":white_check_mark: Year channel iterations complete!",
            )
            return

        await new_first_year_channel.set_permissions(
            guest_role,
            read_messages=True,
            send_messages=True,
        )

        await initial_message.edit(content=(
            ":white_check_mark: Year channel iterations complete "
            "but no year channel category was found!"
        ))
