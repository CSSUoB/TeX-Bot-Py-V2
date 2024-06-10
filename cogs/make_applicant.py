"""Contains cog classes for making the user an applicant."""

from collections.abc import Sequence
from typing import Final

__all__: Sequence[str] = ("BaseMakeApplicantCog","MakeApplicantCommandCog")

import logging
from logging import Logger

import discord

from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")

class BaseMakeApplicantCog(TeXBotBaseCog):
    """
    Base making-applicant cog container class.

    Defines the methods for making users into group-applicants, that are called by
    child cog container classes.
    """

    async def _perform_make_applicant(self, ctx: TeXBotApplicationContext, applicant_member: discord.Member) -> None:  # noqa: E501
        """Perform the actual process of making the user into a group-applicant."""
        main_guild: discord.Guild = ctx.bot.main_guild
        applicant_role: discord.Role = await ctx.bot.applicant_role
        guest_role: discord.Role = await ctx.bot.guest_role

        intro_channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            name="introductions",
        )

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Attempting to make user an Applicant... :hourglass:",
            ephemeral=True,
        )


        AUDIT_MESSAGE: Final[str] = f"{ctx.user} used TeX Bot Command \"Make User Applicant\""


        await applicant_member.add_roles(applicant_role, reason=AUDIT_MESSAGE)

        logger.debug("Applicant role given to user %s", applicant_member)

        if guest_role in applicant_member.roles:
            await applicant_member.remove_roles(guest_role, reason=AUDIT_MESSAGE)
            logger.debug("Removed Guest role from user %s", applicant_member)


        tex_emoji: discord.Emoji | None = self.bot.get_emoji(743218410409820213)
        if not tex_emoji:
            tex_emoji = discord.utils.get(main_guild.emojis, name="TeX")

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
                            "has blocked the bot.",
                            recent_message.author,
                        )
                    break

        await initial_response.edit(content=":white_check_mark: User is now an applicant.")


class MakeApplicantCommandCog(BaseMakeApplicantCog):
    """Cog class that defines the /make_applicant command."""

    @staticmethod
    async def autocomplete_get_all_members(ctx: TeXBotApplicationContext) -> set[discord.OptionChoice]: # noqa: E501
        """
        Autocomplete callable that generates the set of all members in the server.

        This list of selectable members is used in any of the make_applicant slash commands.
        """
        guild: discord.Guild = ctx.bot.main_guild

        members: set[discord.Member] = {member for member in guild.members if not member.bot}

        return {
            discord.OptionChoice(name=member.name, value=str(member.id))
            for member
            in members
        }


    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
            name="make_user_applicant",
            description=(
                "Gives the user @Applicant role and removes the Guest if present."
            ),
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to make an Applicant",
        input_type=str,
        required=True,
        parameter_name="str_applicant_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def make_applicant(self, ctx: TeXBotApplicationContext, str_applicant_member_id: str) -> None:  # noqa: E501
        """
        Definition & callback response of the "make_user_applicant" command.

        This command gives the specified user the applicant role while
        removing the guest role if they have it.
        """
        member_id_not_integer_error: ValueError
        try:
            applicant_member: discord.Member = await self.bot.get_member_from_str_id(
                str_applicant_member_id,
            )
        except ValueError as member_id_not_integer_error:
            await self.command_send_error(ctx, message=member_id_not_integer_error.args[0])
            return

        await self._perform_make_applicant(ctx, applicant_member)


    @discord.user_command(name="Make User Applicant") #type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def make_user_applicant(self, ctx: TeXBotApplicationContext, member: discord.Member) -> None: # noqa: E501
        """
        Definition and callback response of the give_user_applicant_role user-context command.

        This command will simply give the user the applicant role if it exists.
        If the user already has the guest role, this will be removed.
        """
        await self._perform_make_applicant(ctx, member)

    @discord.MessageCommand(name="Make Message Author Applicant") # type: ignore[misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def make_message_author_applicant(self, ctx: TeXBotApplicationContext, message: discord.Message) -> None:  # noqa: E501
        """
        Definition of the "make_message_author_applicant" message-context command.

        This command executes the same process as the user context command but will
        also react with a wave emoji to the message that was used.
        """
        try:
            member: discord.Member = await self.bot.get_member_from_str_id(
                str(message.author.id),
            )
        except ValueError:
            await ctx.respond((
                ":information_source: No changes made. User cannot be given "
                "the Applicant role because they have left the server"
                ":information_source:"
                ),
                ephemeral=True,
            )

        await self._perform_make_applicant(ctx, member)