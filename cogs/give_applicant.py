"""Contains cog classes for giving the applicant role."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import logging
from logging import Logger

import discord

from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")

class GiveApplicantCommandCog(TeXBotBaseCog):
    """Cog class that defines the /give_applicant command."""

    @discord.user_command(name="Give Applicant Role") #type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def give_user_applicant_role(self, ctx: TeXBotApplicationContext, member: discord.Member) -> None: # noqa: E501
        """
        Definition and callback response of the give_user_applicant_role user-context command.

        This command will simply give the user the applicant role if it exists.
        If the user already has the guest role, this will be removed.
        """
        applicant_role: discord.Role = await ctx.bot.applicant_role
        guest_role: discord.Role = await ctx.bot.guest_role

        await member.add_roles(
            applicant_role,
            reason=f"{ctx.user} used TeX Bot User Command \"give_user_applicant_role\"",
        )

        if guest_role in member.roles:
            await member.remove_roles(
                guest_role,
                reason=f"{ctx.user} used TeX Bot User Command \"give_user_applicant_role\"",
            )

    @discord.MessageCommand(name="Give Applicant Role") # type: ignore[misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def give_message_author_applicant_role(self, ctx: TeXBotApplicationContext, message: discord.Message) -> None:  # noqa: E501
        """
        Definition of the "give_message_author_applicant_role" message-context command.

        This command executes the same process as the user context command but will
        also react with a wave emoji to the message that was used.
        """
        applicant_role: discord.Role = await ctx.bot.applicant_role
        guest_role: discord.Role = await ctx.bot.guest_role

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            ":hourglass: Processing... :hourglass:",
            ephemeral=True,
        )

        main_guild: discord.Guild = self.bot.main_guild

        try:
            member: discord.Member = await self.bot.get_member_from_str_id(
                str(message.author.id),
            )
        except ValueError:
            await initial_response.edit(
                content=(
                ":information_source: No changes made. User cannot be given "
                "the Applicant role because they have left the server"
                ":information_source:"
            ),
        )

        tex_emoji: discord.Emoji | None = self.bot.get_emoji(743218410409820213)
        if not tex_emoji:
            tex_emoji = discord.utils.get(main_guild.emojis, name="TeX")

        try:
            if tex_emoji:
                await message.add_reaction(tex_emoji)

            await message.add_reaction("👋")
        except discord.Forbidden as forbidden_error:
            if "90001" not in str(forbidden_error):
                raise forbidden_error from forbidden_error

            logger.info(
                "Failed to add reactions because the user, %s, "
                "has blocked the bot.",
                message.author,
            )

        await member.add_roles(
            applicant_role,
            reason=f"{ctx.user} used TeX Bot Message Command \"give_user_applicant_role\"",
        )

        if guest_role in member.roles:
            await member.remove_roles(
                guest_role,
                reason=f"{ctx.user} used TeX Bot User Command \"give_user_applicant_role\"",
            )
