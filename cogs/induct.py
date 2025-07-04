"""Contains cog classes for any induction interactions."""

import contextlib
import logging
import random
from typing import TYPE_CHECKING

import discord

from config import settings
from db.core.models import IntroductionReminderOptOutMember
from exceptions import (
    ApplicantRoleDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    GuestRoleDoesNotExistError,
    GuildDoesNotExistError,
    MemberRoleDoesNotExistError,
)
from utils import CommandChecks, TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final, Literal

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext

__all__: "Sequence[str]" = (
    "BaseInductCog",
    "EnsureMembersInductedCommandCog",
    "InductContextCommandsCog",
    "InductSendMessageCog",
    "InductSlashCommandCog",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class InductSendMessageCog(TeXBotBaseCog):
    """Cog class that defines the "/induct" command and its call-back method."""

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        Send a welcome message to this member's DMs & remove introduction reminder flags.

        These post-induction actions are only applied to users that have just been inducted as
        a guest into your group's Discord guild.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild

        if before.guild != main_guild or after.guild != main_guild or before.bot or after.bot:
            return

        try:
            guest_role: discord.Role = await self.bot.guest_role
        except GuestRoleDoesNotExistError:
            return

        if guest_role in before.roles or guest_role not in after.roles:
            return

        with contextlib.suppress(IntroductionReminderOptOutMember.DoesNotExist):
            await (
                await IntroductionReminderOptOutMember.objects.aget(
                    discord_member__discord_id=before.id
                )
            ).adelete()

        reminder_message: discord.Message
        async for reminder_message in after.history():
            MESSAGE_IS_INTRODUCTION_REMINDER: bool = bool(
                ("joined the " in reminder_message.content)
                and (" Discord guild but have not yet introduced" in reminder_message.content)
                and reminder_message.author.bot
            )
            if MESSAGE_IS_INTRODUCTION_REMINDER:
                await reminder_message.delete(
                    reason="Delete introduction reminders after member is inducted."
                )

        user_type: Literal["guest", "member"]
        try:
            user_type = "member" if await self.bot.member_role in after.roles else "guest"
        except MemberRoleDoesNotExistError:
            user_type = "guest"

        messages_to_send: list[str] = [
            (
                f"**Congrats on joining the {self.bot.group_short_name} Discord server "
                f"as a {user_type}!** "
                "You now have access to communicate in all the public channels.\n\n"
                "Some things to do to get started:\n"
                f"1. Check out our rules in {
                    await self.bot.get_mention_string(self.bot.rules_channel)
                }\n"
                f"2. Head to {
                    await self.bot.get_mention_string(self.bot.roles_channel)
                } and click on the icons to get optional roles like pronouns and year groups\n"
                "3. Change your nickname to whatever you wish others to refer to you as "
                "(You can do this by right-clicking your name in the members-list "
                'to the right & selecting "Edit Server Profile").'
            )
        ]

        if user_type != "member":
            messages_to_send.append(
                f"You can also get yourself an annual membership "
                f"to {self.bot.group_full_name} for only £5! "
                f"Just head to {settings['PURCHASE_MEMBERSHIP_URL']}. "
                "You'll get awesome perks like a free T-shirt:shirt:, "
                "access to member only events:calendar_spiral: and a cool green name on "
                f"the {self.bot.group_short_name} Discord server:green_square:! "
                f"Checkout all the perks at {settings['MEMBERSHIP_PERKS_URL']}"
            )

        try:
            message_to_send: str
            for message_to_send in messages_to_send:
                await after.send(message_to_send)
        except discord.Forbidden:
            logger.info(
                "Failed to open DM channel to user %s so no welcome message was sent.", after
            )


class BaseInductCog(TeXBotBaseCog):
    """
    Base user-induction cog container class.

    Defines the methods for inducting users that are called by
    child user-induction cog container classes.
    """

    async def get_random_welcome_message(
        self, induction_member: discord.User | discord.Member | None = None
    ) -> str:
        """Get & format a random welcome message."""
        random_welcome_message: str = random.choice(tuple(settings["WELCOME_MESSAGES"]))  # noqa: S311

        if "<User>" in random_welcome_message:
            if not induction_member:
                return await self.get_random_welcome_message(induction_member)

            random_welcome_message = random_welcome_message.replace(
                "<User>", induction_member.mention
            )

        if "<Committee>" in random_welcome_message:
            try:
                committee_role_mention: str = (await self.bot.committee_role).mention
            except CommitteeRoleDoesNotExistError:
                return await self.get_random_welcome_message(induction_member)
            else:
                random_welcome_message = random_welcome_message.replace(
                    "<Committee>", committee_role_mention
                )

        if "<Purchase_Membership_URL>" in random_welcome_message:
            if not settings["PURCHASE_MEMBERSHIP_URL"]:
                return await self.get_random_welcome_message(induction_member)

            random_welcome_message = random_welcome_message.replace(
                "<Purchase_Membership_URL>", settings["PURCHASE_MEMBERSHIP_URL"]
            )

        if "<Group_Name>" in random_welcome_message:
            random_welcome_message = random_welcome_message.replace(
                "<Group_Name>", self.bot.group_short_name
            )

        return random_welcome_message.strip()

    async def _perform_induction(
        self,
        ctx: "TeXBotApplicationContext",
        induction_member: discord.Member,
        *,
        silent: bool,
    ) -> None:
        """Perform the actual process of inducting a member by giving them the Guest role."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        guest_role: discord.Role = await self.bot.guest_role

        await ctx.defer(ephemeral=True)
        async with ctx.typing():
            logger.debug("Inducting member %s, silent=%s", induction_member, silent)

            INDUCT_AUDIT_MESSAGE: Final[str] = (
                f'{ctx.user} used TeX Bot slash-command: "/induct"'
            )

            intro_channel: discord.TextChannel | None = discord.utils.get(
                main_guild.text_channels, name="introductions"
            )

            if induction_member.bot:
                await self.command_send_error(
                    ctx, message="Member cannot be inducted because they are a bot."
                )
                return

            if guest_role in induction_member.roles:
                await ctx.respond(
                    content=(
                        ":information_source: No changes made. "
                        "User has already been inducted. :information_source:"
                    ),
                    ephemeral=True,
                )
                return

            if not silent:
                await (await self.bot.general_channel).send(
                    f"{await self.get_random_welcome_message(induction_member)} :tada:\n"
                    f"Remember to grab your roles in {
                        await self.bot.get_mention_string(self.bot.roles_channel)
                    } and say hello to everyone here! :wave:"
                )

            await induction_member.add_roles(guest_role, reason=INDUCT_AUDIT_MESSAGE)

            news_role: discord.Role | None = discord.utils.get(main_guild.roles, name="News")
            if news_role and news_role not in induction_member.roles:
                await induction_member.add_roles(news_role, reason=INDUCT_AUDIT_MESSAGE)

            try:
                applicant_role: discord.Role = await ctx.bot.applicant_role
            except ApplicantRoleDoesNotExistError:
                pass
            else:
                if applicant_role in induction_member.roles:
                    await induction_member.remove_roles(
                        applicant_role, reason=INDUCT_AUDIT_MESSAGE
                    )

            tex_emoji: discord.Emoji | None = self.bot.get_emoji(743218410409820213)
            if not tex_emoji:
                tex_emoji = discord.utils.get(main_guild.emojis, name="TeX")

            if intro_channel:
                recent_message: discord.Message
                for recent_message in await intro_channel.history(limit=30).flatten():
                    if recent_message.author.id == induction_member.id:
                        try:
                            if tex_emoji:
                                await recent_message.add_reaction(tex_emoji)
                            await recent_message.add_reaction("👋")
                        except discord.Forbidden as e:
                            if "90001" not in str(e):
                                raise e from e

                            logger.info(
                                (
                                    "Failed to add reactions because the user, %s, "
                                    "has blocked TeX-Bot."
                                ),
                                recent_message.author,
                            )
                        break

            await ctx.followup.send(
                content=":white_check_mark: User inducted successfully.", ephemeral=True
            )


class InductSlashCommandCog(BaseInductCog):
    """Cog class that defines the "/induct" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_members(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of available selectable members.

        This list of selectable members is used in any of the "induct" slash-command options
        that have a member input-type.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            guest_role: discord.Role = await ctx.bot.guest_role
        except (GuildDoesNotExistError, GuestRoleDoesNotExistError):
            return set()

        members: set[discord.Member] = {
            member
            for member in main_guild.members
            if not member.bot and guest_role not in member.roles
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
        name="induct",
        description=(
            "Gives a user the @Guest role, then sends a message in #general saying hello."
        ),
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to induct.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_induct_member_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="silent",
        description="Triggers whether a message is sent or not.",
        input_type=bool,
        default=False,
        required=False,
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def induct(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", str_induct_member_id: str, *, silent: bool
    ) -> None:
        """
        Definition & callback response of the "induct" command.

        The "induct" command inducts a given member into your group's Discord guild
        by giving them the "Guest" role.
        """
        member_id_not_integer_error: ValueError
        try:
            induct_member: discord.Member = await self.bot.get_member_from_str_id(
                str_induct_member_id
            )
        except ValueError as member_id_not_integer_error:
            await self.command_send_error(ctx, message=member_id_not_integer_error.args[0])
            return

        await self._perform_induction(ctx, induct_member, silent=silent)


class InductContextCommandsCog(BaseInductCog):
    """Cog class to define the context-menu induction commands and their call-back methods."""

    @discord.user_command(name="Induct User")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def non_silent_user_induct(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", member: discord.Member
    ) -> None:
        """
        Definition & callback response of the "non_silent_induct" user-context-command.

        The "non_silent_induct" command executes the same process
        as the "induct" slash-command, using the user-context-menu.
        Therefore, it will induct a given member into your group's Discord guild
        by giving them the "Guest" role.
        """
        await self._perform_induction(ctx, member, silent=False)

    @discord.user_command(name="Silently Induct User")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def silent_user_induct(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", member: discord.Member
    ) -> None:
        """
        Definition & callback response of the "silent_induct" user-context-command.

        The "silent_induct" command executes the same process as the "induct" slash-command,
        using the user-context-menu.
        Therefore, it will induct a given member into your group's Discord guild
        by giving them the "Guest" role, only without broadcasting a welcome message.
        """
        await self._perform_induction(ctx, member, silent=True)

    @discord.message_command(name="Induct Message Author")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def non_silent_message_induct(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", message: discord.Message
    ) -> None:
        """
        Definition and callback response of the "non_silent_induct" message-context-command.

        The "non_silent_induct" command executes the same process
        as the "induct" slash-command, using the message-context-menu.
        Therefore, it will induct a given member into your group's Discord guild
        by giving them the "Guest" role.
        """
        try:
            member: discord.Member = await self.bot.get_member_from_str_id(
                str(message.author.id)
            )
        except ValueError:
            await ctx.respond(
                (
                    ":information_source: No changes made. User cannot be inducted "
                    "because they have left the server "
                    ":information_source:"
                ),
                ephemeral=True,
            )
            return

        await self._perform_induction(ctx, member, silent=False)


class EnsureMembersInductedCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/ensure-members-inducted" command and call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="ensure-members-inducted",
        description="Ensures all users with the @Member role also have the @Guest role.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def ensure_members_inducted(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """
        Definition & callback response of the "ensure_members_inducted" command.

        The "ensure_members_inducted" command ensures that users
        within your group's Discord guild that have the "Member" role
        have also been given the "Guest" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        member_role: discord.Role = await self.bot.member_role
        guest_role: discord.Role = await self.bot.guest_role

        await ctx.defer(ephemeral=True)

        changes_made: bool = False

        member: discord.Member
        for member in main_guild.members:
            if guest_role in member.roles:
                continue

            if member_role in member.roles and guest_role not in member.roles:
                changes_made = True
                await member.add_roles(
                    guest_role,
                    reason=(
                        f'{ctx.user} used TeX Bot slash-command: "/ensure-members-inducted"'
                    ),
                )

        await ctx.respond(
            (
                "All members successfully inducted"
                if changes_made
                else "No members required inducting"
            ),
            ephemeral=True,
        )
