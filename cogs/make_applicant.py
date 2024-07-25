"""Contains cog classes for making a user into an applicant."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "BaseMakeApplicantCog",
    "MakeApplicantSlashCommandCog",
    "MakeApplicantContextCommandsCog",
)


import logging
from logging import Logger
from typing import Final

import discord

from exceptions.does_not_exist import ApplicantRoleDoesNotExistError, GuildDoesNotExistError
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class BaseMakeApplicantCog(TeXBotBaseCog):
    """
    Base making-applicant cog container class.

    Defines the methods for making users into group-applicants that are called by
    child cog container classes.
    """

    async def _perform_make_applicant(self, ctx: TeXBotApplicationContext, applicant_member: discord.Member) -> None:  # noqa: E501
        """Perform the actual process of making the user into a group-applicant."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = ctx.bot.main_guild
        applicant_role: discord.Role = await ctx.bot.applicant_role
        guest_role: discord.Role = await ctx.bot.guest_role

        if applicant_role in applicant_member.roles:
            await ctx.respond("User is already an applicant! Command aborted.")
            return

        if applicant_member.bot:
            await self.command_send_error(ctx, message="Cannot make a bot user an applicant!")
            return

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Attempting to make user an applicant... :hourglass:",
            ephemeral=True,
        )

        AUDIT_MESSAGE: Final[str] = f"{ctx.user} used TeX-Bot Command \"Make User Applicant\""

        if guest_role in applicant_member.roles:
            await applicant_member.remove_roles(guest_role, reason=AUDIT_MESSAGE)
            logger.debug("Removed Guest role from user %s", applicant_member)

        await applicant_member.add_roles(applicant_role, reason=AUDIT_MESSAGE)
        logger.debug("Applicant role given to user %s", applicant_member)

        tex_emoji: discord.Emoji | None = self.tex_bot.get_emoji(743218410409820213)
        if not tex_emoji:
            tex_emoji = discord.utils.get(main_guild.emojis, name="TeX")

        intro_channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            name="introductions",
        )

        if intro_channel:
            recent_message: discord.Message
            for recent_message in await intro_channel.history(limit=30).flatten():
                if recent_message.author.id == applicant_member.id:
                    forbidden_error: discord.Forbidden
                    try:
                        if tex_emoji:
                            await recent_message.add_reaction(tex_emoji)
                        await recent_message.add_reaction("👋")
                    except discord.Forbidden as forbidden_error:
                        if "90001" not in str(forbidden_error):
                            raise forbidden_error from forbidden_error

                        logger.info(
                            "Failed to add reactions because the user, %s, "
                            "has blocked TeX-Bot.",
                            recent_message.author,
                        )
                    break

        await initial_response.edit(content=":white_check_mark: User is now an applicant.")


class MakeApplicantSlashCommandCog(BaseMakeApplicantCog):
    """Cog class that defines the "/make_applicant" slash-command."""

    @staticmethod
    async def autocomplete_get_members(ctx: TeXBotApplicationContext) -> set[discord.OptionChoice]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable members.

        This list of selectable members is used in any of the "make_applicant" slash-command
        options that have a member input-type.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            applicant_role: discord.Role = await ctx.bot.applicant_role
        except (GuildDoesNotExistError, ApplicantRoleDoesNotExistError):
            return set()

        members: set[discord.Member] = {
            member
            for member
            in main_guild.members
            if not member.bot and applicant_role not in member.roles
        }

        if not ctx.value or ctx.value.startswith("@"):
            return {
                discord.OptionChoice(name=f"@{member.name}", value=str(member.id))
                for member
                in members
            }

        return {
            discord.OptionChoice(name=member.name, value=str(member.id))
            for member
            in members
        }

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="make-applicant",
        description=(
            "Gives the user @Applicant role and removes the @Guest role if present."
        ),
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to make an Applicant.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_applicant_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def make_applicant(self, ctx: TeXBotApplicationContext, str_applicant_member_id: str) -> None:  # noqa: E501
        """
        Definition & callback response of the "make_applicant" command.

        The "make_applicant" command gives the specified user the "Applicant" role and
        removes the "Guest" role if they have it.
        """
        member_id_not_integer_error: ValueError
        try:
            applicant_member: discord.Member = await self.tex_bot.get_member_from_str_id(
                str_applicant_member_id,
            )
        except ValueError as member_id_not_integer_error:
            await self.command_send_error(ctx, message=member_id_not_integer_error.args[0])
            return

        await self._perform_make_applicant(ctx, applicant_member)


class MakeApplicantContextCommandsCog(BaseMakeApplicantCog):
    """Cog class that defines the "/make_applicant" context commands."""

    @discord.user_command(name="Make Applicant")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def user_make_applicant(self, ctx: TeXBotApplicationContext, member: discord.Member) -> None:  # noqa: E501
        """
        Definition and callback response of the "make_applicant" user-context-command.

        The "make_applicant" user-context-command executes the same process as
        the "make_applicant" slash-command and thus gives the specified user the
        "Applicant" role and removes the "Guest" role if they have it.
        """
        await self._perform_make_applicant(ctx, member)

    @discord.message_command(name="Make Message Author Applicant")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def message_make_applicant(self, ctx: TeXBotApplicationContext, message: discord.Message) -> None:  # noqa: E501
        """
        Definition of the "message_make_applicant" message-context-command.

        The "make_applicant" message-context-command executes the same process as
        the "make_applicant" slash-command and thus gives the specified user the
        "Applicant" role and removes the "Guest" role if they have it.
        """
        try:
            member: discord.Member = await self.tex_bot.get_member_from_str_id(
                str(message.author.id),
            )
        except ValueError:
            await ctx.respond((
                ":information_source: No changes made. User cannot be made into an applicant "
                "because they have left the server :information_source:"
                ),
                ephemeral=True,
            )
            return

        await self._perform_make_applicant(ctx, member)
