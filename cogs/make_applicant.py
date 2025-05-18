"""Contains cog classes for making a user into an applicant."""

import logging
from typing import TYPE_CHECKING

import discord

from exceptions.does_not_exist import ApplicantRoleDoesNotExistError, GuildDoesNotExistError
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = (
    "BaseMakeApplicantCog",
    "MakeApplicantContextCommandsCog",
    "MakeApplicantSlashCommandCog",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class BaseMakeApplicantCog(TeXBotBaseCog):
    """
    Base making-applicant cog container class.

    Defines the methods for making users into group-applicants that are called by
    child cog container classes.
    """

    async def _perform_make_applicant(
        self, ctx: "TeXBotApplicationContext", applicant_member: discord.Member
    ) -> None:
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

        await ctx.defer(ephemeral=True)
        async with ctx.typing():
            AUDIT_MESSAGE: Final[str] = (
                f'{ctx.user} used TeX-Bot Command "Make User Applicant"'
            )

            if guest_role in applicant_member.roles:
                await applicant_member.remove_roles(guest_role, reason=AUDIT_MESSAGE)
                logger.debug("Removed Guest role from user %s", applicant_member)

            await applicant_member.add_roles(applicant_role, reason=AUDIT_MESSAGE)
            logger.debug("Applicant role given to user %s", applicant_member)

            tex_emoji: discord.Emoji | None = self.bot.get_emoji(743218410409820213)
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
                        try:
                            if tex_emoji:
                                await recent_message.add_reaction(tex_emoji)
                            await recent_message.add_reaction("👋")
                        except discord.Forbidden as e:
                            if "90001" not in str(e):
                                raise e from e

                            logger.info(
                                "Failed to add reactions because the user, %s, "
                                "has blocked TeX-Bot.",
                                recent_message.author,
                            )
                        break

            try:
                await applicant_member.send(
                    content=(
                        f"Congratulations {applicant_member.mention}, you've "
                        "now been given applicant access to the CSS Discord server! "
                        "As you are not yet a student at the University, "
                        "you only have limited access to participate in certain channels.\n\n"
                        "If you are already a student and your induction as an applicant was"
                        " a mistake, please contact a committee member.\n\n"
                        "If you have already purchased a membership, you can run the "
                        "`/makemember` command, and you will be given full access by "
                        f"{self.bot.user.display_name if self.bot.user else 'TeX-Bot'}.\n\n"
                        "Some things to do to get started:\n"
                        "1. Check out our rules in "
                        f"{await self.bot.get_mention_string(self.bot.rules_channel)}\n"
                        "2. Head to "
                        f"{await self.bot.get_mention_string(self.bot.roles_channel)}"
                        " and click on the icons to get optional roles like "
                        "pronouns and year group\n"
                        "3. Change your nickname to whatever "
                        "you wish others to refer to you as"
                    ),
                )
            except discord.Forbidden:
                logger.warning(
                    "Failed to send applicant induction DM to user %s", applicant_member
                )

            await ctx.followup.send(
                content=":white_check_mark: User is now an applicant.",
                ephemeral=True,
            )


class MakeApplicantSlashCommandCog(BaseMakeApplicantCog):
    """Cog class that defines the "/make-applicant" slash-command."""

    @staticmethod
    async def autocomplete_get_members(
        ctx: "TeXBotApplicationContext",
    ) -> set[discord.OptionChoice]:
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
            for member in main_guild.members
            if not member.bot and applicant_role not in member.roles
        }

        if not ctx.value or ctx.value.startswith("@"):
            return {
                discord.OptionChoice(name=f"@{member.name}", value=str(member.id))
                for member in members
            }

        return {
            discord.OptionChoice(name=member.name, value=str(member.id)) for member in members
        }

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="make-applicant",
        description="Gives the user @Applicant role and removes the @Guest role if present.",
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
    async def make_applicant(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", str_applicant_member_id: str
    ) -> None:
        """
        Definition & callback response of the "make_applicant" command.

        The "make_applicant" command gives the specified user the "Applicant" role and
        removes the "Guest" role if they have it.
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


class MakeApplicantContextCommandsCog(BaseMakeApplicantCog):
    """Cog class that defines the context menu make-applicant commands."""

    @discord.user_command(name="Make Applicant")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def user_make_applicant(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", member: discord.Member
    ) -> None:
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
    async def message_make_applicant(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", message: discord.Message
    ) -> None:
        """
        Definition of the "message_make_applicant" message-context-command.

        The "make_applicant" message-context-command executes the same process as
        the "make_applicant" slash-command and thus gives the specified user the
        "Applicant" role and removes the "Guest" role if they have it.
        """
        try:
            member: discord.Member = await self.bot.get_member_from_str_id(
                str(message.author.id),
            )
        except ValueError:
            await ctx.respond(
                content=(
                    ":information_source: "
                    "No changes made. User cannot be made into an applicant "
                    "because they have left the server :information_source:"
                ),
                ephemeral=True,
            )
            return

        await self._perform_make_applicant(ctx, member)
