"""Contains cog classes for any strike interactions."""

import asyncio
import contextlib
import datetime
import re
from collections.abc import Mapping
from typing import Final

import discord
from discord.ext import commands
from discord.ui import View

from config import settings
from db.core.models import MemberStrikes
from exceptions import (
    GuildDoesNotExist,
    RulesChannelDoesNotExist,
    StrikeTrackingError,
)
from utils import (
    CommandChecks,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)
from utils.error_capture_decorators import (
    capture_guild_does_not_exist_error,
    capture_strike_tracking_error,
)
from utils.message_sender_components import (
    ChannelMessageSender,
    MessageSenderComponent,
    ResponseMessageSender,
)


async def perform_moderation_action(strike_user: discord.Member, strikes: int, committee_member: discord.Member | discord.User) -> None:  # noqa: E501
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
        await strike_user.timeout_for(
            datetime.timedelta(hours=24),
            reason=MODERATION_ACTION_REASON
        )

    elif strikes == 2:
        await strike_user.kick(reason=MODERATION_ACTION_REASON)

    elif strikes == 3:
        await strike_user.ban(reason=MODERATION_ACTION_REASON)


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


class ConfirmManualModerationView(View):
    """A discord.View to confirm manually applying a moderation action."""

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.red,
        custom_id="yes_manual_moderation_action"
    )
    async def yes_manual_moderation_action_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """
        Delete the message associated with the view, when the Yes button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        await interaction.response.edit_message(delete_after=0)

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.grey,
        custom_id="no_manual_moderation_action"
    )
    async def no_manual_moderation_action_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """
        Delete the message associated with the view, when the No button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        await interaction.response.edit_message(delete_after=0)


class ConfirmStrikesOutOfSyncWithBanView(View):
    """A discord.View containing two buttons to confirm banning a member with > 3 strikes."""

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.red,
        custom_id="yes_out_of_sync_ban_member"
    )
    async def yes_out_of_sync_ban_member_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """
        Delete the message associated with the view, when the Yes button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        await interaction.response.edit_message(delete_after=0)

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.grey,
        custom_id="no_out_of_sync_ban_member"
    )
    async def no_out_of_sync_ban_member_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """
        Delete the message associated with the view, when the No button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        await interaction.response.edit_message(delete_after=0)


class BaseStrikeCog(TeXBotBaseCog):
    """
    Base strike cog container class.

    Defines the methods for striking users that are called
    by child strike cog container classes.
    """

    SUGGESTED_ACTIONS: Final[Mapping[int, str]] = {1: "time-out", 2: "kick", 3: "ban"}

    async def _send_strike_user_message(self, strike_user: discord.User | discord.Member, member_strikes: MemberStrikes) -> None:  # noqa: E501
        # noinspection PyUnusedLocal
        rules_channel_mention: str = "`#welcome`"
        with contextlib.suppress(RulesChannelDoesNotExist):
            rules_channel_mention = (await self.bot.rules_channel).mention

        includes_ban_message: str = (
            (
                "\nBecause you now have been given 3 strikes, you have been banned from "
                "the CSS Discord server and we have contacted the Guild of Students for "
                "further action & advice."
            )
            if member_strikes.strikes >= 3
            else ""
        )

        actual_strike_amount: int = (
            member_strikes.strikes
            if member_strikes.strikes < 3
            else 3
        )

        await strike_user.send(
            "Hi, a recent incident occurred in which you may have broken one or more of "
            "the CSS Discord server's rules.\nWe have increased the number of strikes "
            f"associated with your account to {actual_strike_amount} "
            "and the corresponding moderation action will soon be applied to you. "
            "To find what moderation action corresponds to which strike level, "
            "you can view the CSS Discord server moderation document "
            f"[here](<{settings.MODERATION_DOCUMENT_URL}>)\nPlease ensure you have read "
            f"the rules in {rules_channel_mention} so that your future behaviour adheres "
            f"to them.{includes_ban_message}\n\nA committee member will be in contact "
            "with you shortly, to discuss this further."
        )

    async def _confirm_perform_moderation_action(self, message_sender_component: MessageSenderComponent, interaction_user: discord.User, strike_user: discord.Member, confirm_strike_message: str, actual_strike_amount: int, button_callback_channel: discord.TextChannel | discord.DMChannel) -> None:  # noqa: E501
        await message_sender_component.send(
            content=confirm_strike_message,
            view=ConfirmStrikeMemberView()
        )

        button_interaction: discord.Interaction = await self.bot.wait_for(
            "interaction",
            check=lambda interaction: (
                interaction.type == discord.InteractionType.component
                and interaction.user == interaction_user
                and interaction.channel == button_callback_channel
                and "custom_id" in interaction.data
                and interaction.data["custom_id"] in {"yes_strike_member", "no_strike_member"}
            )
        )

        if button_interaction.data["custom_id"] == "no_strike_member":  # type: ignore[index, typeddict-item]
            await message_sender_component.send(
                f"Aborted performing {self.SUGGESTED_ACTIONS[actual_strike_amount]} action "
                f"on {strike_user.mention}."
            )
            return

        await perform_moderation_action(
            strike_user,
            actual_strike_amount,
            committee_member=interaction_user
        )

        await message_sender_component.send(
            f"Successfully performed {self.SUGGESTED_ACTIONS[actual_strike_amount]} action "
            f"on {strike_user.mention}."
        )

    async def _confirm_increase_strike(self, message_sender_component: MessageSenderComponent, interaction_user: discord.User, strike_user: discord.User | discord.Member, member_strikes: MemberStrikes, button_callback_channel: discord.TextChannel | discord.DMChannel, *, perform_action: bool) -> None:  # noqa: E501
        if perform_action and isinstance(strike_user, discord.User):
            STRIKE_USER_TYPE_ERROR_MESSAGE: Final[str] = (
                "Cannot perform moderation action on non-guild member."
            )
            raise TypeError(STRIKE_USER_TYPE_ERROR_MESSAGE)

        if member_strikes.strikes < 3:
            member_strikes.strikes += 1
            await member_strikes.asave()

        await self._send_strike_user_message(strike_user, member_strikes)

        confirm_strike_message: str = (
            f"Successfully increased {strike_user.mention}'s strikes to "
            f"{member_strikes.strikes}."
        )

        if perform_action:
            confirm_strike_message = (
                f"{confirm_strike_message}\nThe suggested moderation action is to "
                f"{self.SUGGESTED_ACTIONS[member_strikes.strikes]} the user. Would you "
                "like me to perform this action for you?"
            )

        if member_strikes.strikes > 3:
            confirm_strike_message = (
                f"{strike_user.mention}'s number of strikes was not increased "
                f"because they already had {member_strikes.strikes}. "
                "How did this happen?"
            )
            if perform_action:
                confirm_strike_message = (
                    f"{confirm_strike_message}\nHaving more than 3 strikes suggests that "
                    "the user should be banned. Would you like me "
                    "to perform this action for you?"
                )

        if not perform_action:
            sent_message: discord.Message = await message_sender_component.send(
                content=(
                    f"{confirm_strike_message}\n"
                    "**Please ensure you use the `/strike` command in future!**\n"
                    "ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"  # noqa: RUF001
                    f"""{
                        discord.utils.format_dt(
                            discord.utils.utcnow() + datetime.timedelta(minutes=2),
                            "R"
                        )
                    }"""
                )
            )
            await asyncio.sleep(118)
            await sent_message.delete()
            return

        assert isinstance(strike_user, discord.Member)

        await self._confirm_perform_moderation_action(
            message_sender_component,
            interaction_user,
            strike_user,
            confirm_strike_message,
            (member_strikes.strikes if member_strikes.strikes < 3 else 3),
            button_callback_channel
        )

    async def _command_perform_strike(self, ctx: TeXBotApplicationContext, strike_member: discord.Member) -> None:  # noqa: E501
        """
        Perform the actual process of giving a member an additional strike.

        Also calls the process of performing the appropriate moderation action,
        given the new number of strikes that the member has.
        """
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

        await self._confirm_increase_strike(
            message_sender_component=ResponseMessageSender(ctx),
            interaction_user=ctx.user,
            strike_user=strike_member,
            member_strikes=member_strikes,
            button_callback_channel=ctx.channel,
            perform_action=True
        )


class ManualModerationCog(BaseStrikeCog):
    """
    Cog class defining the event listeners for manually applying moderation actions.

    When Committee members manually apply moderation actions on users, these event listeners
    will be run to confirm the actions are tracked.
    """

    async def get_confirmation_message_channel(self, user: discord.User | discord.Member) -> discord.DMChannel | discord.TextChannel:  # noqa: E501
        """
        Retrieve the correct channel to send the strike confirmation message to.

        This is based upon the MANUAL_MODERATION_WARNING_MESSAGE_LOCATION config setting value.
        """
        unable_to_determine_confirmation_message_channel: bool = bool(
            user.bot
            and settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] == "DM"
        )
        if unable_to_determine_confirmation_message_channel:
            INDETERMINABLE_CHANNEL_MESSAGE: Final[str] = (
                "Cannot determine channel to send manual-moderation warning messages to"
            )
            raise StrikeTrackingError(INDETERMINABLE_CHANNEL_MESSAGE)

        if settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] == "DM":
            raw_user: discord.User | None = (
                self.bot.get_user(user.id)
                if isinstance(user, discord.Member)
                else user
            )
            if not raw_user:
                raise StrikeTrackingError

            dm_confirmation_message_channel: discord.DMChannel = (
                await raw_user.create_dm()
            )
            if not dm_confirmation_message_channel.recipient:
                dm_confirmation_message_channel.recipient = raw_user

            return dm_confirmation_message_channel

        guild_confirmation_message_channel: discord.TextChannel | None = discord.utils.get(
            self.bot.css_guild.text_channels,
            name=settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"]
        )
        if not guild_confirmation_message_channel:
            CHANNEL_DOES_NOT_EXIST_MESSAGE: Final[str] = (
                "The channel "
                f"""{settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"]!r} """
                "does not exist, so cannot be used as the location "
                "for sending manual-moderation warning messages"
            )
            raise StrikeTrackingError(CHANNEL_DOES_NOT_EXIST_MESSAGE)

        return guild_confirmation_message_channel

    @capture_strike_tracking_error
    async def _confirm_manual_add_strike(self, strike_user: discord.User | discord.Member, action: discord.AuditLogAction) -> None:  # noqa: E501
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
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
                if _audit_log_entry.target == strike_user
            )
        except StopIteration:
            IRRETRIEVABLE_AUDIT_LOG_MESSAGE: Final[str] = (
                f"Unable to retrieve audit log entry of {str(action)!r} action "
                f"on user {str(strike_user)!r}"
            )
            raise StrikeTrackingError(IRRETRIEVABLE_AUDIT_LOG_MESSAGE) from None

        if not audit_log_entry.user:
            raise StrikeTrackingError

        confirmation_message_channel: discord.DMChannel | discord.TextChannel = await self.get_confirmation_message_channel(  # noqa: E501
            audit_log_entry.user
        )

        MODERATION_ACTIONS: Final[Mapping[discord.AuditLogAction, str]] = {
            discord.AuditLogAction.member_update: "timed-out",
            discord.AuditLogAction.kick: "kicked",
            discord.AuditLogAction.ban: "banned"
        }

        member_strikes: MemberStrikes = (
            await MemberStrikes.objects.aget_or_create(
                hashed_member_id=MemberStrikes.hash_member_id(strike_user.id)
            )
        )[0]

        strikes_out_of_sync_with_ban: bool = bool(
            (action != discord.AuditLogAction.ban and member_strikes.strikes >= 3)
            or (action == discord.AuditLogAction.ban and member_strikes.strikes > 3)
        )
        if strikes_out_of_sync_with_ban:
            out_of_sync_ban_confirmation_message: discord.Message = await confirmation_message_channel.send(  # noqa: E501
                content=(
                    f"Hi {audit_log_entry.user.display_name}, "
                    f"I just noticed that you {MODERATION_ACTIONS[action]} "
                    f"{strike_user.mention}. Because you did this manually "
                    "(rather than using my `/strike` command), I could not automatically "
                    f"keep track of the moderation action to apply. "
                    f"My records show that {strike_user.mention} previously had 3 strikes. "
                    f"This suggests that {strike_user.mention} should be banned. "
                    "Would you like me to send them the moderation alert message "
                    "and perform this action for you?"
                ),
                view=ConfirmStrikesOutOfSyncWithBanView()
            )

            out_of_sync_ban_button_interaction: discord.Interaction = await self.bot.wait_for(
                "interaction",
                check=lambda interaction: (
                    interaction.type == discord.InteractionType.component
                    and interaction.user == audit_log_entry.user
                    and interaction.channel == confirmation_message_channel
                    and "custom_id" in interaction.data
                    and interaction.data["custom_id"] in {
                        "yes_out_of_sync_ban_member",
                        "no_out_of_sync_ban_member"
                    }
                )
            )

            if out_of_sync_ban_button_interaction.data["custom_id"] == "no_out_of_sync_ban_member":  # type: ignore[index, typeddict-item] # noqa: E501
                await out_of_sync_ban_confirmation_message.delete()
                aborted_out_of_sync_ban_message: discord.Message = await confirmation_message_channel.send(  # noqa: E501
                    f"Aborted performing ban action upon {strike_user.mention}. "
                    "(This manual moderation action has not been tracked.)\n"
                    "ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"  # noqa: RUF001
                    f"""{
                        discord.utils.format_dt(
                            discord.utils.utcnow() + datetime.timedelta(minutes=2),
                            "R"
                        )
                    }"""
                )
                await asyncio.sleep(118)
                await aborted_out_of_sync_ban_message.delete()
                return

            await self._send_strike_user_message(strike_user, member_strikes)
            await css_guild.ban(
                strike_user,
                reason=(
                    f"**{audit_log_entry.user.display_name} synced moderation action "
                    "with number of strikes**"
                )
            )
            success_out_of_sync_ban_message: discord.Message = await confirmation_message_channel.send(  # noqa: E501
                f"Successfully banned {strike_user.mention}.\n"
                "**Please ensure you use the `/strike` command in future!**"
                "\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"  # noqa: RUF001
                f"""{
                    discord.utils.format_dt(
                        discord.utils.utcnow() + datetime.timedelta(minutes=2),
                        "R"
                    )
                }"""
            )
            await asyncio.sleep(118)
            await success_out_of_sync_ban_message.delete()
            return

        confirmation_message: discord.Message = await confirmation_message_channel.send(
            content=(
                f"Hi {audit_log_entry.user.display_name}, "
                f"I just noticed that you {MODERATION_ACTIONS[action]} "
                f"{strike_user.mention}. Because you did this manually "
                "(rather than using my `/strike` command), I could not automatically "
                f"keep track of the correct moderation action to apply. "
                f"Would you like me to increase {strike_user.mention}'s strikes "
                f"from {member_strikes.strikes} to {member_strikes.strikes + 1} "
                "and send them the moderation alert message?"
            ),
            view=ConfirmManualModerationView()
        )

        button_interaction: discord.Interaction = await self.bot.wait_for(
            "interaction",
            check=lambda interaction: (
                interaction.type == discord.InteractionType.component
                and interaction.user == audit_log_entry.user
                and interaction.channel == confirmation_message_channel
                and "custom_id" in interaction.data
                and interaction.data["custom_id"] in {
                    "yes_manual_moderation_action",
                    "no_manual_moderation_action"
                }
            )
        )

        if button_interaction.data["custom_id"] == "no_manual_moderation_action":  # type: ignore[index, typeddict-item]
            await confirmation_message.delete()
            aborted_strike_message: discord.Message = await confirmation_message_channel.send(
                f"Aborted increasing {strike_user.mention}'s strikes "
                "& sending moderation alert message. "
                "(This manual moderation action has not been tracked.)\n"
                "ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"  # noqa: RUF001
                f"""{
                    discord.utils.format_dt(
                        discord.utils.utcnow() + datetime.timedelta(minutes=2),
                        "R"
                    )
                }"""
            )
            await asyncio.sleep(118)
            await aborted_strike_message.delete()
            return

        interaction_user: discord.User | None = self.bot.get_user(audit_log_entry.user.id)
        if not interaction_user:
            raise StrikeTrackingError

        await self._confirm_increase_strike(
            message_sender_component=ChannelMessageSender(confirmation_message_channel),
            interaction_user=interaction_user,
            strike_user=strike_user,
            member_strikes=member_strikes,
            button_callback_channel=confirmation_message_channel,
            perform_action=False
        )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Flag manually applied timeout & track strikes accordingly."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        css_guild: discord.Guild = self.bot.css_guild

        if before.guild != css_guild or after.guild != css_guild or before.bot or after.bot:
            return

        if not after.timed_out or before.timed_out == after.timed_out:
            return

        await self._confirm_manual_add_strike(
            strike_user=after,
            action=discord.AuditLogAction.member_update
        )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_remove(self, member: discord.Member) -> None:
        """Flag manually applied kick & track strikes accordingly."""
        if member.guild != self.bot.css_guild or member.bot:
            return

        await self._confirm_manual_add_strike(
            strike_user=member,
            action=discord.AuditLogAction.kick
        )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member) -> None:  # noqa: E501
        """Flag manually applied ban & track strikes accordingly."""
        if guild != self.bot.css_guild or user.bot:
            return

        await self._confirm_manual_add_strike(
            strike_user=user,
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
            "Gives a user an additional strike, "
            "then performs the appropriate moderation action."
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
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def strike(self, ctx: TeXBotApplicationContext, str_strike_member_id: str) -> None:
        """
        Definition & callback response of the "strike" command.

        The "strike" command adds an additional strike to the given member, then performs the
        appropriate moderation action to the member, according to the new number of strikes.
        """
        try:
            strike_member: discord.Member = await self.bot.get_member_from_str_id(
                str_strike_member_id
            )
        except ValueError as e:
            await self.send_error(ctx, message=e.args[0])
            return

        await self._command_perform_strike(ctx, strike_member)


class StrikeUserCommandCog(BaseStrikeCog):
    """Cog class that defines the context menu strike command & its call-back method."""

    @discord.user_command(name="Strike User")  # type: ignore[no-untyped-call, misc]
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def user_strike(self, ctx: TeXBotApplicationContext, member: discord.Member) -> None:
        """Call the _strike command, providing the required command arguments."""
        await self._command_perform_strike(ctx, member)
