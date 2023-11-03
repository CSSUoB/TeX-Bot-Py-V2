"""Contains cog classes for any induction interactions."""

import contextlib
import random
import re
from typing import Literal

import discord
from discord.ext import commands

from cogs._command_checks import Checks
from cogs._utils import (
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotCog,
    capture_guild_does_not_exist_error,
)
from config import settings
from db.core.models import IntroductionReminderOptOutMember
from exceptions import (
    CommitteeRoleDoesNotExist,
    GuestRoleDoesNotExist,
    GuildDoesNotExist,
    MemberRoleDoesNotExist,
    RolesChannelDoesNotExist,
    RulesChannelDoesNotExist,
    UserNotInCSSDiscordServer,
)


class InductSendMessageCog(TeXBotCog):
    """Cog class that defines the "/induct" command and its call-back method."""

    @TeXBotCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        Send a welcome message to this member's DMs & remove introduction reminder flags.

        These post-induction actions are only applied to users that have just been inducted as
        a guest into the CSS Discord server.
        """
        guild: discord.Guild = self.bot.css_guild

        if before.guild != guild or after.guild != guild or before.bot or after.bot:
            return

        try:
            guest_role: discord.Role = await self.bot.guest_role
        except GuestRoleDoesNotExist:
            return

        if guest_role in before.roles or guest_role not in after.roles:
            return

        try:
            introduction_reminder_opt_out_member: IntroductionReminderOptOutMember = await IntroductionReminderOptOutMember.objects.aget(  # noqa: E501
                hashed_member_id=IntroductionReminderOptOutMember.hash_member_id(
                    before.id
                )
            )
        except IntroductionReminderOptOutMember.DoesNotExist:
            pass
        else:
            await introduction_reminder_opt_out_member.adelete()

        async for message in after.history():
            message_is_introduction_reminder: bool = (
                (
                    "joined the CSS Discord server but have not yet introduced"
                ) in message.content and message.author.bot
            )
            if message_is_introduction_reminder:
                await message.delete(
                    reason="Delete introduction reminders after member is inducted."
                )

        # noinspection PyUnusedLocal
        rules_channel_mention: str = "`#welcome`"
        with contextlib.suppress(RulesChannelDoesNotExist):
            rules_channel_mention = (await self.bot.rules_channel).mention

        # noinspection PyUnusedLocal
        roles_channel_mention: str = "#roles"
        with contextlib.suppress(RolesChannelDoesNotExist):
            roles_channel_mention = (await self.bot.roles_channel).mention

        user_type: Literal["guest", "member"] = "guest"
        with contextlib.suppress(MemberRoleDoesNotExist):
            if await self.bot.member_role in after.roles:
                user_type = "member"

        await after.send(
            f"**Congrats on joining the CSS Discord server as a {user_type}!**"
            " You now have access to contribute to all the public channels."
            "\n\nSome things to do to get started:"
            f"\n1. Check out our rules in {rules_channel_mention}"
            f"\n2. Head to {roles_channel_mention} and click on the icons to get"
            " optional roles like pronouns and year groups"
            "\n3. Change your nickname to whatever you wish others to refer to you as"
            " (You can do this by right-clicking your name in the members list"
            " to the right & selecting \"Edit Server Profile\")"
        )
        if user_type != "member":
            await after.send(
                "You can also get yourself an annual membership to CSS for only £5!"
                " Just head to https://cssbham.com/join."
                " You'll get awesome perks like a free T-shirt:shirt:,"
                " access to member only events:calendar_spiral:"
                " & a cool green name on the CSS Discord server:green_square:!"
                " Checkout all the perks at https://cssbham.com/membership."
            )


class BaseInductCog(TeXBotCog):
    """
    Base user-induction cog container class.

    Defines the methods for inducting users that are called by
    child user-induction cog container classes.
    """

    async def _perform_induction(self, ctx: TeXBotApplicationContext, induction_member: discord.Member, *, silent: bool) -> None:  # noqa: E501
        """Perform the actual process of inducting a member by giving them the Guest role."""
        guest_role: discord.Role = await self.bot.guest_role

        if guest_role in induction_member.roles:
            await ctx.respond(
                (
                    ":information_source: No changes made. User has already been inducted."
                    " :information_source:"
                ),
                ephemeral=True
            )
            return

        if induction_member.bot:
            await self.send_error(
                ctx,
                message="Member cannot be inducted because they are a bot."
            )
            return

        if not silent:
            general_channel: discord.TextChannel = await self.bot.general_channel

            # noinspection PyUnusedLocal
            roles_channel_mention: str = "#roles"
            with contextlib.suppress(RolesChannelDoesNotExist):
                roles_channel_mention = (await self.bot.roles_channel).mention

            # noinspection PyUnusedLocal
            committee_role_mention: str = "@Committee"
            with contextlib.suppress(CommitteeRoleDoesNotExist):
                committee_role_mention = (await self.bot.committee_role).mention

            await general_channel.send(
                f"""{
                    random.choice(settings["WELCOME_MESSAGES"]).replace(
                        "<User>",
                        induction_member.mention
                    ).replace("<@Committee>", committee_role_mention).strip()
                } :tada:\nRemember to grab your roles in {roles_channel_mention}"""
                f""" and say hello to everyone here! :wave:"""
            )

        await induction_member.add_roles(
            guest_role,
            reason=f"{ctx.user} used TeX Bot slash-command: \"/induct\""
        )

        applicant_role: discord.Role | None = discord.utils.get(
            self.bot.css_guild.roles,
            name="Applicant"
        )

        if applicant_role and applicant_role in induction_member.roles:
            await induction_member.remove_roles(
                applicant_role,
                reason=f"{ctx.user} used TeX Bot slash-command: \"/induct\""
            )

        await ctx.respond("User inducted successfully.", ephemeral=True)


class InductCommandCog(BaseInductCog):
    """Cog class that defines the "/induct" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_members(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable members.

        This list of selectable members is used in any of the "induct" slash-command options
        that have a member input-type.
        """
        try:
            guild: discord.Guild = ctx.bot.css_guild
        except GuildDoesNotExist:
            return set()

        members: set[discord.Member] = {member for member in guild.members if not member.bot}

        try:
            guest_role: discord.Role = await ctx.bot.guest_role
        except GuestRoleDoesNotExist:
            return set()
        else:
            members = {member for member in members if guest_role not in member.roles}

        if not ctx.value or re.match(r"\A@.*\Z", ctx.value):
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
        name="induct",
        description=(
            "Gives a user the @Guest role, then sends a message in #general saying hello."
        )
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to induct.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_induct_member_id"
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="silent",
        description="Triggers whether a message is sent or not.",
        input_type=bool,
        default=False,
        required=False
    )
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def induct(self, ctx: TeXBotApplicationContext, str_induct_member_id: str, *, silent: bool) -> None:  # noqa: E501
        """
        Definition & callback response of the "induct" command.

        The "induct" command inducts a given member into the CSS Discord server by giving them
        the "Guest" role.
        """
        str_induct_member_id = str_induct_member_id.replace("<@", "").replace(">", "")

        if not re.match(r"\A\d{17,20}\Z", str_induct_member_id):
            await self.send_error(
                ctx,
                message=f"\"{str_induct_member_id}\" is not a valid user ID."
            )
            return

        induct_user: discord.User | None = self.bot.get_user(int(str_induct_member_id))
        if induct_user:
            try:
                induct_member: discord.Member = await self.bot.get_css_user(induct_user)
            except UserNotInCSSDiscordServer:
                induct_user = None

        if not induct_user:
            await self.send_error(
                ctx,
                message=f"Member with ID \"{str_induct_member_id}\" does not exist."
            )
            return

        # noinspection PyUnboundLocalVariable
        await self._perform_induction(ctx, induct_member, silent=silent)


class InductUserCommandsCog(BaseInductCog):
    """Cog class that defines the context menu induction commands & their call-back methods."""

    @discord.user_command(name="Induct User")  # type: ignore[no-untyped-call, misc]
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def non_silent_induct(self, ctx: TeXBotApplicationContext, member: discord.Member) -> None:  # noqa: E501
        """
        Definition & callback response of the "non_silent_induct" user-context-command.

        The "non_silent_induct" command executes the same process as the
        "induct" slash-command, and thus inducts a given member into the CSS Discord server by
        giving them the "Guest" role, only without broadcasting a welcome message.
        """
        await self._perform_induction(ctx, member, silent=False)

    @discord.user_command(name="Silently Induct User")  # type: ignore[no-untyped-call, misc]
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def silent_induct(self, ctx: TeXBotApplicationContext, member: discord.Member) -> None:  # noqa: E501
        """
        Definition & callback response of the "silent_induct" user-context-command.

        The "silent_induct" command executes the same process as the "induct" slash-command,
        and thus inducts a given member into the CSS Discord server by giving them the
        "Guest" role.
        """
        await self._perform_induction(ctx, member, silent=True)


class EnsureMembersInductedCommandCog(TeXBotCog):
    """Cog class that defines the "/ensure-members-inducted" command and call-back method."""

    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="ensure-members-inducted",
        description="Ensures all users with the @Member role also have the @Guest role."
    )
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def ensure_members_inducted(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "ensure_members_inducted" command.

        The "ensure_members_inducted" command ensures that users within the CSS Discord server
        that have the "Member" role have also been given the "Guest" role.
        """
        css_guild: discord.Guild = self.bot.css_guild
        member_role: discord.Role = await self.bot.member_role
        guest_role: discord.Role = await self.bot.guest_role

        await ctx.defer(ephemeral=True)

        changes_made: bool = False

        member: discord.Member
        for member in css_guild.members:
            if guest_role in member.roles:
                continue

            if member_role in member.roles and guest_role not in member.roles:
                changes_made = True
                await member.add_roles(
                    guest_role,
                    reason=(
                        f"{ctx.user} used TeX Bot slash-command: \"/ensure-members-inducted\""
                    )
                )

        await ctx.respond(
            (
                "All members successfully inducted"
                if changes_made
                else "No members required inducting"
            ),
            ephemeral=True
        )
