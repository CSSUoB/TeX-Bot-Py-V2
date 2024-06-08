"""Contains cog classes for giving the applicant role."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import logging
from logging import Logger

import discord

from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")

class BaseMakeApplicantCog(TeXBotBaseCog):
    """
    Base Make Applicant cog container class.

    Defines the methods for making users applicants that are called by
    child cog container classes.
    """

    async def _perform_make_applicant(self, ctx: TeXBotApplicationContext, applicant_member: discord.Member) -> None:  # noqa: E501
        """Perform the actual process of making the user an applicant."""
        applicant_role: discord.Role = await ctx.bot.applicant_role
        guest_role: discord.Role = await ctx.bot.applicant_role
        main_guild: discord.Guild = ctx.bot.main_guild

        intro_channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            name="introductions",
        )

        audit_message: str = f"{ctx.user} used TeX Bot Command \"Make User Applicant\""

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Attempting to make user an Applicant... :hourglass:",
            ephemeral=True,
        )

        await applicant_member.add_roles(
            applicant_role,
            reason=audit_message,
        )
        logger.debug("Applicant role given to user %s", applicant_member)

        if guest_role in applicant_member.roles:
            await applicant_member.remove_roles(
                guest_role,
                reason=audit_message,
            )
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

        await initial_response.edit(content=":white_check_mark: User inducted successfully.")


class MakeApplicantCommandCog(BaseMakeApplicantCog):
    """Cog class that defines the /make_applicant command."""

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
