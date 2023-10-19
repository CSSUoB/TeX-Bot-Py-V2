"""Contains cog classes for any strike interactions."""

import datetime
import logging
import re
from typing import TYPE_CHECKING, Final

import discord
from discord.ui import View

from cogs._utils import (
    TeXBotAutocompleteContext,
    TeXBotCog,
    capture_guild_does_not_exist_error,
)
from config import settings
from db.core.models import MemberStrikes
from exceptions import CommitteeRoleDoesNotExist, GuildDoesNotExist

if TYPE_CHECKING:
    from collections.abc import Mapping


async def perform_moderation_action(strike_member: discord.Member, strikes: int, committee_member: discord.Member) -> None:  # noqa: E501
    """
    Perform the actual process of applying a moderation action to a member.

    The appropriate moderation action to apply is determined by the number of strikes
    the member has. The CSS Discord moderation document outlines which
    number of strikes corresponds to which moderation action.
    """
    if not 1 <= strikes <= 3:
        INVALID_STRIKE_AMOUNT_MESSAGE: Final[str] = (
            "'strikes' cannot be greater than 3 or less than 1"
        )
        raise ValueError(INVALID_STRIKE_AMOUNT_MESSAGE)

    MODERATION_ACTION_REASON: Final[str] = (
        f"**{committee_member.display_name}** used `/strike`"
    )

    if strikes == 1:
        await strike_member.timeout_for(
            datetime.timedelta(hours=24),
            reason=MODERATION_ACTION_REASON
        )

    elif strikes == 2:
        await strike_member.kick(reason=MODERATION_ACTION_REASON)

    elif strikes == 3:
        await strike_member.ban(reason=MODERATION_ACTION_REASON)


class ConfirmStrikeMemberView(View):
    """A discord.View containing two buttons to confirm giving the member a strike."""

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.red,
        custom_id="yes_strike_member"
    )
    async def yes_strike_member_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """
        Delete the message associated with the view, when the Yes button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by the command that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        await interaction.response.edit_message(delete_after=0)

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.grey,
        custom_id="no_strike_member"
    )
    async def no_strike_member_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """
        Delete the message associated with the view, when the No button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by the command that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        await interaction.response.edit_message(delete_after=0)


class BaseStrikeCog(TeXBotCog):
    """
    Base strike cog container class.

    Defines the methods for striking users that are called
    by child strike cog container classes.
    """

    async def _perform_strike(self, ctx: discord.ApplicationContext, strike_member: discord.Member, guild: discord.Guild) -> None:  # noqa: E501
        """
        Perform the actual process of giving a member an additional strike.

        Also calls the process of performing the appropriate moderation action,
        given the new number of strikes that the member has.
        """
        committee_role: discord.Role | None = await self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                logging_message=CommitteeRoleDoesNotExist()
            )
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = committee_role.mention

            await self.send_error(
                ctx,
                message=f"Only {committee_role_mention} members can run this command."
            )
            return

        if strike_member.bot:
            await self.send_error(
                ctx,
                message="Member cannot be given an additional strike because they are a bot."
            )
            return

        member_strikes: MemberStrikes = (
            await MemberStrikes.objects.aget_or_create(
                hashed_member_id=MemberStrikes.hash_member_id(strike_member.id)
            )
        )[0]

        if member_strikes.strikes < 3:
            member_strikes.strikes += 1
            await member_strikes.asave()

        rules_channel_mention: str = "`#welcome`"
        rules_channel: discord.TextChannel | None = await self.bot.rules_channel
        if rules_channel:
            rules_channel_mention = rules_channel.mention

        includes_ban_message: str = ""
        if member_strikes.strikes >= 3:
            includes_ban_message = (
                "\nBecause you now have been given 3 strikes, you have been banned from"
                " the CSS Discord server and we have contacted the Guild of Students for"
                " further action & advice."
            )

        actual_strike_amount: int = (
            member_strikes.strikes if member_strikes.strikes < 3 else 3
        )

        await strike_member.send(
            "Hi, a recent incident occurred in which you may have broken one or more of"
            " the CSS Discord server's rules.\nWe have increased the number of strikes"
            f" associated with your account to {actual_strike_amount}"
            " and the corresponding moderation action will soon be applied to you."
            " To find what moderation action corresponds to which strike level,"
            " you can view the CSS Discord server moderation document"
            f" [here]({settings.MODERATION_DOCUMENT_URL})\nPlease ensure you have read"
            f" the rules in {rules_channel_mention} so that your future behaviour adheres"
            f" to them.{includes_ban_message}\n\nA committee member will be in contact"
            " with you shortly, to discuss this further."
        )

        SUGGESTED_ACTIONS: Final[Mapping[int, str]] = {1: "time-out", 2: "kick", 3: "ban"}

        confirm_strike_message: str = (
            f"Successfully increased {strike_member.mention}'s strikes to"
            f" {member_strikes.strikes}.\nThe suggested moderation action is to"
            f" {SUGGESTED_ACTIONS[member_strikes.strikes]} the user. Would you"
            " like the bot to perform this action for you?"
        )

        if member_strikes.strikes > 3:
            confirm_strike_message = (
                f"{strike_member.mention}'s number of strikes was not increased"
                f" because they already had {member_strikes.strikes}."
                " How did this happen?\nHaving more than 3 strikes suggests that"
                " the user should be banned. Would you like the bot to perform"
                " this action for you?"
            )

        await ctx.respond(
            content=confirm_strike_message,
            view=ConfirmStrikeMemberView(),
            ephemeral=True
        )

        button_interaction: discord.Interaction = await self.bot.wait_for(
            "interaction",
            check=lambda interaction: (
                interaction.type == discord.InteractionType.component
                and interaction.user == ctx.user
                and interaction.channel == ctx.channel
                and "custom_id" in interaction.data
                and interaction.data["custom_id"] in {
                    "yes_strike_member",
                    "no_strike_member"
                }
            )
        )

        if button_interaction.data["custom_id"] == "no_strike_member":  # type: ignore[index, typeddict-item]
            await ctx.respond(
                f"Aborted performing {SUGGESTED_ACTIONS[actual_strike_amount]} action"
                f" on {strike_member.mention}.",
                ephemeral=True
            )
            return

        await perform_moderation_action(
            strike_member,
            actual_strike_amount,
            committee_member=interaction_member
        )

        await ctx.respond(
            f"Successfully performed {SUGGESTED_ACTIONS[actual_strike_amount]} action"
            f" on {strike_member.mention}.",
            ephemeral=True
        )


class ManualModerationCog(BaseStrikeCog):
    """
    Cog class defining the event listeners for manually applying moderation actions.

    When Committee members manually apply moderation actions on users, these event listeners
    will be run to confirm the actions are tracked.
    """

    async def _confirm_manual_add_strike(self, target: discord.User | discord.Member, action: discord.AuditLogAction) -> None:  # noqa: E501
        css_guild: discord.Guild = self.bot.css_guild
        try:
            # noinspection PyTypeChecker
            audit_log_entry: discord.AuditLogEntry = await anext(
                _audit_log_entry
                async for _audit_log_entry
                in css_guild.audit_logs(
                    after=discord.utils.utcnow() - datetime.timedelta(minutes=1),
                    action=action
                )
                if _audit_log_entry.target == target
            )
        except StopIteration:
            return

    @TeXBotCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        css_guild: discord.Guild = self.bot.css_guild
        if before.guild != css_guild or after.guild != css_guild or before.bot or after.bot:
            return

        if not after.timed_out:
            return

        await self._confirm_manual_add_strike(
            target=after,
            action=discord.AuditLogAction.member_update
        )

    @TeXBotCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_remove(self, member: discord.Member) -> None:
        css_guild: discord.Guild = self.bot.css_guild
        if member.guild != css_guild or member.bot:
            return

        await self._confirm_manual_add_strike(
            target=member,
            action=discord.AuditLogAction.kick
        )

    @TeXBotCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member) -> None:  # noqa: E501
        css_guild: discord.Guild = self.bot.css_guild
        if guild != css_guild or user.bot:
            return

        await self._confirm_manual_add_strike(
            target=user,
            action=discord.AuditLogAction.ban
        )


class StrikeCommandCog(BaseStrikeCog):
    """Cog class that defines the "/strike" command and its call-back method."""

    @staticmethod
    async def strike_autocomplete_get_members(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable members.

        This list of selectable members is used in any of the "strike" slash-command options
        that have a member input-type.
        """
        try:
            guild: discord.Guild = ctx.bot.css_guild
        except GuildDoesNotExist:
            return set()

        members: set[discord.Member] = {member for member in guild.members if not member.bot}

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
        name="strike",
        description=(
            "Gives a user an additional strike,"
            " then performs the appropriate moderation action."
        )
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to give a strike to.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(strike_autocomplete_get_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_strike_member_id"
    )
    async def strike(self, ctx: discord.ApplicationContext, str_strike_member_id: str) -> None:
        """
        Definition & callback response of the "strike" command.

        The "strike" command adds an additional strike to the given member, then performs the
        appropriate moderation action to the member, according to the new number of strikes.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        str_strike_member_id = str_strike_member_id.replace("<@", "").replace(">", "")

        if not re.match(r"\A\d{17,20}\Z", str_strike_member_id):
            await self.send_error(
                ctx,
                message=f"\"{str_strike_member_id}\" is not a valid user ID."
            )
            return

        strike_member_id: int = int(str_strike_member_id)

        strike_member: discord.Member | None = guild.get_member(strike_member_id)
        if not strike_member:
            await self.send_error(
                ctx,
                message=f"Member with ID \"{strike_member_id}\" does not exist."
            )
            return

        await self._perform_strike(ctx, strike_member, guild)


class StrikeUserCommandCog(BaseStrikeCog):
    """Cog class that defines the context menu strike command & its call-back method."""

    @discord.user_command(name="Strike User")  # type: ignore[no-untyped-call, misc]
    async def strike(self, ctx: discord.ApplicationContext, member: discord.Member) -> None:
        """Call the _strike command, providing the required command arguments."""
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            raise

        await self._perform_strike(ctx, member, guild)
