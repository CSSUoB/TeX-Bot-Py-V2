"""Contains cog classes for any strike interactions."""

import asyncio
import contextlib
import datetime
import logging
import re
from typing import TYPE_CHECKING

import discord
from asyncstdlib.builtins import any as asyncany
from discord.ui import View

from config import settings
from db.core.models import DiscordMemberStrikes
from exceptions import (
    GuildDoesNotExistError,
    NoAuditLogsStrikeTrackingError,
    StrikeTrackingError,
)
from utils import (
    CommandChecks,
    TeXBotBaseCog,
)
from utils.error_capture_decorators import (
    capture_guild_does_not_exist_error,
    capture_strike_tracking_error,
)
from utils.message_sender_components import (
    ChannelMessageSender,
    ResponseMessageSender,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import (
        TeXBotApplicationContext,
        TeXBotAutocompleteContext,
    )
    from utils.message_sender_components import (
        MessageSavingSenderComponent,
    )

__all__: "Sequence[str]" = (
    "BaseStrikeCog",
    "ConfirmManualModerationView",
    "ConfirmStrikeMemberView",
    "ConfirmStrikesOutOfSyncWithBanView",
    "ManualModerationCog",
    "StrikeCommandCog",
    "StrikeContextCommandsCog",
    "perform_moderation_action",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

FORMATTED_MODERATION_ACTIONS: "Final[Mapping[discord.AuditLogAction, str]]" = {
    discord.AuditLogAction.member_update: "timed-out",
    discord.AuditLogAction.kick: "kicked",
    discord.AuditLogAction.ban: "banned",
    discord.AuditLogAction.auto_moderation_user_communication_disabled: "timed-out",
}


async def perform_moderation_action(
    strike_user: discord.Member, strikes: int, committee_member: discord.Member | discord.User
) -> None:
    """
    Perform the actual process of applying a moderation action to a member.

    The appropriate moderation action to apply is determined by the number of strikes
    the member has. Your group's Discord moderation document should outline which
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
            reason=MODERATION_ACTION_REASON,
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
        custom_id="yes_strike_member",
    )
    async def yes_strike_member_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """
        Delete the message associated with the view when the Yes button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by the command that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        logger.debug('"Yes" button pressed. %s', interaction)
        await interaction.response.edit_message(
            view=None
        )  # NOTE: Despite removing the view within the normal command processing loop, the view also needs to be removed here to prevent an Unknown Webhook error

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.grey,
        custom_id="no_strike_member",
    )
    async def no_strike_member_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """
        Delete the message associated with the view when the No button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by the command that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        logger.debug('"No" button pressed. %s', interaction)
        await interaction.response.edit_message(
            view=None
        )  # NOTE: Despite removing the view within the normal command processing loop, the view also needs to be removed here to prevent an Unknown Webhook error


class ConfirmManualModerationView(View):
    """A discord.View to confirm manually applying a moderation action."""

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.red,
        custom_id="yes_manual_moderation_action",
    )
    async def yes_manual_moderation_action_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """
        Delete the message associated with the view when the Yes button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        logger.debug('"Yes" button pressed. %s', interaction)
        await interaction.response.edit_message(
            view=None
        )  # NOTE: Despite removing the view within the normal command processing loop, the view also needs to be removed here to prevent an Unknown Webhook error

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.grey,
        custom_id="no_manual_moderation_action",
    )
    async def no_manual_moderation_action_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """
        Delete the message associated with the view when the No button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        logger.debug('"No" button pressed. %s', interaction)
        await interaction.response.edit_message(
            view=None
        )  # NOTE: Despite removing the view within the normal command processing loop, the view also needs to be removed here to prevent an Unknown Webhook error


class ConfirmStrikesOutOfSyncWithBanView(View):
    """A discord.View containing two buttons to confirm banning a member with > 3 strikes."""

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.red,
        custom_id="yes_out_of_sync_ban_member",
    )
    async def yes_out_of_sync_ban_member_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """
        Delete the message associated with the view when the Yes button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        logger.debug('"Yes" button pressed. %s', interaction)
        await interaction.response.edit_message(
            view=None
        )  # NOTE: Despite removing the view within the normal command processing loop, the view also needs to be removed here to prevent an Unknown Webhook error

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.grey,
        custom_id="no_out_of_sync_ban_member",
    )
    async def no_out_of_sync_ban_member_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """
        Delete the message associated with the view when the No button is pressed.

        This function is attached as a button's callback, so will run whenever the button
        is pressed.
        The actual handling of the event is done by
        the manual moderation tracker subroutine that sent the view,
        so all that is required is to delete the original message that sent this view.
        """
        logger.debug('"No" button pressed. %s', interaction)
        await interaction.response.edit_message(
            view=None
        )  # NOTE: Despite removing the view within the normal command processing loop, the view also needs to be removed here to prevent an Unknown Webhook error


class BaseStrikeCog(TeXBotBaseCog):
    """
    Base strike cog container class.

    Defines the methods for striking users that are called
    by child strike cog container classes.
    """

    SUGGESTED_ACTIONS: "Final[Mapping[int, str]]" = {1: "time-out", 2: "kick", 3: "ban"}  # noqa: RUF012

    async def _send_strike_user_message(
        self, strike_user: discord.User | discord.Member, member_strikes: DiscordMemberStrikes
    ) -> None:
        try:
            await strike_user.send(
                "Hi, a recent incident occurred in which you may have broken one or more of "
                f"the {self.bot.group_short_name} Discord server's rules.\n"
                "We have increased the number of strikes associated with your account "
                f"to {min(3, member_strikes.strikes)} and "
                "the corresponding moderation action will soon be applied to you. "
                "To find what moderation action corresponds to which strike level, "
                "you can view "
                f"the {self.bot.group_short_name} Discord server moderation document "
                f"[here](<{settings.MODERATION_DOCUMENT_URL}>)\nPlease ensure you have read "
                f"the rules in {await self.bot.get_mention_string(self.bot.rules_channel)} so "
                "that your future behaviour adheres to them."
                f"{
                    (
                        '\nBecause you now have been given 3 strikes, '
                        'you have been banned from '
                        f'the {self.bot.group_short_name} Discord server '
                        f'and we have contacted {self.bot.group_moderation_contact} for '
                        'further action & advice.'
                    )
                    if member_strikes.strikes >= 3
                    else ''
                }\n\n"
                "A committee member will be in contact with you shortly, "
                "to discuss this further."
            )
        except discord.Forbidden:
            logger.warning("Failed to send strike message to %s", strike_user)

    async def _confirm_perform_moderation_action(
        self,
        message_sender_component: "MessageSavingSenderComponent",
        interaction_user: discord.User,
        strike_user: discord.Member,
        confirm_strike_message: str,
        actual_strike_amount: int,
        button_callback_channel: discord.TextChannel | discord.DMChannel,
    ) -> None:
        await message_sender_component.send(
            content=confirm_strike_message,
            view=ConfirmStrikeMemberView(),
        )

        button_interaction: discord.Interaction = await self.bot.wait_for(
            "interaction",
            check=lambda interaction: (
                interaction.type == discord.InteractionType.component
                and interaction.user == interaction_user
                and interaction.channel == button_callback_channel
                and "custom_id" in interaction.data
                and interaction.data["custom_id"] in {"yes_strike_member", "no_strike_member"}
            ),
        )

        if button_interaction.data["custom_id"] == "no_strike_member":  # type: ignore[index, typeddict-item]
            await button_interaction.edit_original_response(
                content=(
                    "Aborted performing "
                    f"{self.SUGGESTED_ACTIONS[actual_strike_amount]} action "
                    f"on {strike_user.mention}."
                ),
                view=None,
            )
            return

        if button_interaction.data["custom_id"] == "yes_strike_member":  # type: ignore[index, typeddict-item]
            await perform_moderation_action(
                strike_user,
                actual_strike_amount,
                committee_member=interaction_user,
            )

            await button_interaction.edit_original_response(
                content=(
                    f"Successfully performed {self.SUGGESTED_ACTIONS[actual_strike_amount]} "
                    f"action on {strike_user.mention}."
                ),
                view=None,
            )
            return

        raise ValueError

    async def _confirm_increase_strike(
        self,
        message_sender_component: "MessageSavingSenderComponent",
        interaction_user: discord.User,
        strike_user: discord.User | discord.Member,
        member_strikes: DiscordMemberStrikes,
        button_callback_channel: discord.TextChannel | discord.DMChannel,
        *,
        perform_action: bool,
    ) -> None:
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
            await message_sender_component.send(
                content=(
                    f"{confirm_strike_message}\n"
                    "**Please ensure you use the `/strike` command in future!**\n"
                    "ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"
                    f"""{
                        discord.utils.format_dt(
                            discord.utils.utcnow() + datetime.timedelta(minutes=2), "R"
                        )
                    }"""
                ),
            )
            await asyncio.sleep(118)
            await message_sender_component.delete()
            return

        if not isinstance(strike_user, discord.Member):
            INCORRECT_STRIKE_USER_TYPE_MESSAGE: Final[str] = (
                f"Incorrect type for {'strike_user'!r}: got {type(strike_user).__name__!r}, "
                f"expected {discord.Member.__name__!r}."
            )
            raise RuntimeError(INCORRECT_STRIKE_USER_TYPE_MESSAGE)  # noqa: TRY004

        await self._confirm_perform_moderation_action(
            message_sender_component,
            interaction_user,
            strike_user,
            confirm_strike_message,
            min(3, member_strikes.strikes),
            button_callback_channel,
        )

    async def _command_perform_strike(
        self, ctx: "TeXBotApplicationContext", strike_member: discord.Member
    ) -> None:
        """
        Perform the actual process of giving a member an additional strike.

        Also calls the process of performing the appropriate moderation action,
        given the new number of strikes that the member has.
        """
        if strike_member.bot:
            await self.command_send_error(
                ctx,
                message="Member cannot be given an additional strike because they are a bot.",
            )
            return

        member_strikes: DiscordMemberStrikes = (
            await DiscordMemberStrikes.objects.aget_or_create(
                discord_id=strike_member.id,
            )
        )[0]

        await self._confirm_increase_strike(
            message_sender_component=ResponseMessageSender(ctx),
            interaction_user=ctx.user,
            strike_user=strike_member,
            member_strikes=member_strikes,
            button_callback_channel=ctx.channel,
            perform_action=True,
        )


class ManualModerationCog(BaseStrikeCog):
    """
    Cog class defining the event listeners for manually applying moderation actions.

    When Committee members manually apply moderation actions on users, these event listeners
    will be run to confirm the actions are tracked.
    """

    async def get_confirmation_message_channel(
        self, user: discord.User | discord.Member
    ) -> discord.DMChannel | discord.TextChannel:
        """
        Retrieve the correct channel to send the strike confirmation message to.

        This is based upon the STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION config setting value.
        """
        if settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"] == "DM":
            if user.bot:
                fetch_log_channel_error: RuntimeError
                try:
                    return await self.bot.fetch_log_channel()
                except RuntimeError as fetch_log_channel_error:
                    raise StrikeTrackingError(
                        str(fetch_log_channel_error),
                    ) from fetch_log_channel_error

            raw_user: discord.User | None = (
                self.bot.get_user(user.id) if isinstance(user, discord.Member) else user
            )
            if not raw_user:
                raise StrikeTrackingError

            dm_confirmation_message_channel: discord.DMChannel = await raw_user.create_dm()
            if not dm_confirmation_message_channel.recipient:
                dm_confirmation_message_channel.recipient = raw_user

            return dm_confirmation_message_channel

        guild_confirmation_message_channel: discord.TextChannel | None = discord.utils.get(
            self.bot.main_guild.text_channels,
            name=settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"],
        )
        if not guild_confirmation_message_channel:
            CHANNEL_DOES_NOT_EXIST_MESSAGE: Final[str] = (
                "The channel "
                f"""{settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"]!r} """
                "does not exist, so cannot be used as the location "
                "for sending manual-moderation warning messages"
            )
            raise StrikeTrackingError(CHANNEL_DOES_NOT_EXIST_MESSAGE)

        return guild_confirmation_message_channel

    @capture_strike_tracking_error
    async def _confirm_manual_add_strike(
        self, strike_user: discord.User | discord.Member, action: discord.AuditLogAction
    ) -> None:
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        committee_role: discord.Role = await self.bot.committee_role

        try:
            audit_log_entry: discord.AuditLogEntry = await anext(
                _audit_log_entry
                async for _audit_log_entry in main_guild.audit_logs(
                    after=discord.utils.utcnow() - datetime.timedelta(minutes=1),
                    action=action,
                )
                if _audit_log_entry.target.id
                == strike_user.id  # NOTE: IDs are checked here rather than the objects themselves as the audit log provides an unusual object type in some cases.
            )
        except (StopIteration, StopAsyncIteration):
            logger.debug("Printing 5 most recent audit logs:")
            debug_audit_log_entry: discord.AuditLogEntry
            async for debug_audit_log_entry in main_guild.audit_logs(limit=5):
                logger.debug(debug_audit_log_entry)

            IRRETRIEVABLE_AUDIT_LOG_MESSAGE: Final[str] = (
                f"Unable to retrieve audit log entry of {str(action)!r} action "
                f"on user {str(strike_user)!r}"
            )
            raise NoAuditLogsStrikeTrackingError(IRRETRIEVABLE_AUDIT_LOG_MESSAGE) from None

        if not audit_log_entry.user:
            raise StrikeTrackingError

        applied_action_user: discord.User | discord.Member = audit_log_entry.user

        if applied_action_user == self.bot.user:
            return

        fetch_log_channel_error: RuntimeError
        try:
            confirmation_message_channel: discord.DMChannel | discord.TextChannel = (
                await self.get_confirmation_message_channel(applied_action_user)
                if applied_action_user != strike_user
                else await self.bot.fetch_log_channel()
            )
        except RuntimeError as fetch_log_channel_error:
            raise StrikeTrackingError(
                str(fetch_log_channel_error),
            ) from fetch_log_channel_error

        member_strikes: DiscordMemberStrikes = (
            await DiscordMemberStrikes.objects.aget_or_create(
                discord_id=strike_user.id,
            )
        )[0]

        STRIKES_OUT_OF_SYNC_WITH_BAN: Final[bool] = bool(
            (action != discord.AuditLogAction.ban and member_strikes.strikes >= 3)
            or (action == discord.AuditLogAction.ban and member_strikes.strikes > 3)
        )
        if STRIKES_OUT_OF_SYNC_WITH_BAN:
            out_of_sync_ban_confirmation_message: discord.Message = await confirmation_message_channel.send(  # noqa: E501
                content=(
                    f"""Hi {
                        applied_action_user.display_name
                        if not applied_action_user.bot and applied_action_user != strike_user
                        else committee_role.mention
                    }, """
                    f"""I just noticed that {
                        "you"
                        if not applied_action_user.bot
                        else f"one of your other bots (namely {applied_action_user.mention})"
                    } {FORMATTED_MODERATION_ACTIONS[action]} {strike_user.mention}. """
                    "Because this moderation action was done manually "
                    "(rather than using my `/strike` command), I could not automatically "
                    f"keep track of the moderation action to apply. "
                    f"My records show that {strike_user.mention} previously had 3 strikes. "
                    f"This suggests that {strike_user.mention} should be banned. "
                    "Would you like me to send them the moderation alert message "
                    "and perform this action for you?"
                ),
                view=ConfirmStrikesOutOfSyncWithBanView(),
            )

            out_of_sync_ban_button_interaction: discord.Interaction = await self.bot.wait_for(
                "interaction",
                check=lambda interaction: (
                    interaction.type == discord.InteractionType.component
                    and (
                        (interaction.user == applied_action_user)
                        if not applied_action_user.bot
                        else (committee_role in interaction.user.roles)
                    )
                    and interaction.channel == confirmation_message_channel
                    and "custom_id" in interaction.data
                    and interaction.data["custom_id"]
                    in {
                        "yes_out_of_sync_ban_member",
                        "no_out_of_sync_ban_member",
                    }
                ),
            )

            if (
                out_of_sync_ban_button_interaction.data["custom_id"]  # type: ignore[index, typeddict-item]
                == "no_out_of_sync_ban_member"
            ):
                await out_of_sync_ban_confirmation_message.edit(
                    content=(
                        f"Aborted performing ban action upon {strike_user.mention}. "
                        "(This manual moderation action has not been tracked.)\n"
                        "ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"
                        f"""{
                            discord.utils.format_dt(
                                discord.utils.utcnow() + datetime.timedelta(minutes=2), "R"
                            )
                        }"""
                    ),
                    view=None,
                )
                await asyncio.sleep(118)
                await out_of_sync_ban_confirmation_message.delete()
                return

            if (
                out_of_sync_ban_button_interaction.data["custom_id"]  # type: ignore[index, typeddict-item]
                == "yes_out_of_sync_ban_member"
            ):
                await self._send_strike_user_message(strike_user, member_strikes)
                await main_guild.ban(
                    strike_user,
                    reason=(
                        f"**{applied_action_user.display_name} synced moderation action "
                        "with number of strikes**"
                    ),
                )
                await out_of_sync_ban_confirmation_message.edit(
                    content=(
                        f"Successfully banned {strike_user.mention}.\n"
                        "**Please ensure you use the `/strike` command in future!**"
                        "\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"
                        f"""{
                            discord.utils.format_dt(
                                discord.utils.utcnow() + datetime.timedelta(minutes=2), "R"
                            )
                        }"""
                    ),
                    view=None,
                )
                await asyncio.sleep(118)
                await out_of_sync_ban_confirmation_message.delete()
                return

            raise ValueError

        confirmation_message: discord.Message = await confirmation_message_channel.send(
            content=(
                f"""Hi {
                    applied_action_user.display_name
                    if not applied_action_user.bot and applied_action_user != strike_user
                    else committee_role.mention
                }, """
                f"""I just noticed that {
                    "you"
                    if not applied_action_user.bot
                    else f"one of your other bots (namely {applied_action_user.mention})"
                } {FORMATTED_MODERATION_ACTIONS[action]} {strike_user.mention}. """
                "Because this moderation action was done manually "
                "(rather than using my `/strike` command), I could not automatically "
                f"keep track of the correct moderation action to apply. "
                f"Would you like me to increase {strike_user.mention}'s strikes "
                f"from {member_strikes.strikes} to {member_strikes.strikes + 1} "
                "and send them the moderation alert message?"
            ),
            view=ConfirmManualModerationView(),
        )

        button_interaction: discord.Interaction = await self.bot.wait_for(
            "interaction",
            check=lambda interaction: (
                interaction.type == discord.InteractionType.component
                and (
                    (interaction.user == applied_action_user)
                    if not applied_action_user.bot
                    else (committee_role in interaction.user.roles)
                )
                and interaction.channel == confirmation_message_channel
                and "custom_id" in interaction.data
                and interaction.data["custom_id"]
                in {
                    "yes_manual_moderation_action",
                    "no_manual_moderation_action",
                }
            ),
        )

        if button_interaction.data["custom_id"] == "no_manual_moderation_action":  # type: ignore[index, typeddict-item]
            await confirmation_message.edit(
                content=(
                    f"Aborted increasing {strike_user.mention}'s strikes "
                    "& sending moderation alert message. "
                    "(This manual moderation action has not been tracked.)\n"
                    "ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ"
                    f"""{
                        discord.utils.format_dt(
                            discord.utils.utcnow() + datetime.timedelta(minutes=2), "R"
                        )
                    }"""
                ),
                view=None,
            )
            await asyncio.sleep(118)
            await confirmation_message.delete()
            return

        if button_interaction.data["custom_id"] == "yes_manual_moderation_action":  # type: ignore[index, typeddict-item]
            interaction_user: discord.User | None = self.bot.get_user(
                applied_action_user.id,
            )
            if not interaction_user:
                raise StrikeTrackingError

            await self._confirm_increase_strike(
                message_sender_component=ChannelMessageSender(confirmation_message_channel),
                interaction_user=interaction_user,
                strike_user=strike_user,
                member_strikes=member_strikes,
                button_callback_channel=confirmation_message_channel,
                perform_action=False,
            )

        raise ValueError

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Flag manually applied timeout and track strikes accordingly."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild

        if before.guild != main_guild or after.guild != main_guild or before.bot or after.bot:
            return

        if not after.timed_out or before.timed_out == after.timed_out:
            return

        audit_log_entry: discord.AuditLogEntry
        async for audit_log_entry in main_guild.audit_logs(limit=5):
            FOUND_CORRECT_AUDIT_LOG_ENTRY: bool = audit_log_entry.target.id == after.id and (
                audit_log_entry.action
                == discord.AuditLogAction.auto_moderation_user_communication_disabled
            )
            if FOUND_CORRECT_AUDIT_LOG_ENTRY:
                await self._confirm_manual_add_strike(
                    strike_user=after,
                    action=audit_log_entry.action,
                )
                return

        await self._confirm_manual_add_strike(
            strike_user=after,
            action=discord.AuditLogAction.member_update,
        )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_remove(self, member: discord.Member) -> None:
        """Flag manually applied kick and track strikes accordingly."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild

        MEMBER_REMOVED_BECAUSE_OF_MANUALLY_APPLIED_KICK: Final[bool] = bool(
            member.guild == self.bot.main_guild
            and not member.bot
            and not await asyncany(ban.user == member async for ban in main_guild.bans())
        )
        if not MEMBER_REMOVED_BECAUSE_OF_MANUALLY_APPLIED_KICK:
            return

        with contextlib.suppress(NoAuditLogsStrikeTrackingError):
            await self._confirm_manual_add_strike(
                strike_user=member,
                action=discord.AuditLogAction.kick,
            )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_ban(
        self, guild: discord.Guild, user: discord.User | discord.Member
    ) -> None:
        """Flag manually applied ban and track strikes accordingly."""
        if guild != self.bot.main_guild or user.bot:
            return

        await self._confirm_manual_add_strike(
            strike_user=user,
            action=discord.AuditLogAction.ban,
        )


class StrikeCommandCog(BaseStrikeCog):
    """Cog class that defines the "/strike" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_members(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of available selectable members.

        This list of selectable members is used in any of the "strike" slash-command options
        that have a member input-type.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except GuildDoesNotExistError:
            return set()

        members: set[discord.Member] = {
            member for member in main_guild.members if not member.bot
        }

        if not ctx.value or re.fullmatch(r"\A@.*\Z", ctx.value):
            return {
                discord.OptionChoice(name=f"@{member.name}", value=str(member.id))
                for member in members
            }

        return {
            discord.OptionChoice(name=member.name, value=str(member.id)) for member in members
        }

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="strike",
        description=(
            "Gives a user an additional strike, "
            "then performs the appropriate moderation action."
        ),
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to give a strike to.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_strike_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def strike(self, ctx: "TeXBotApplicationContext", str_strike_member_id: str) -> None:  # type: ignore[misc]
        """
        Definition & callback response of the "strike" command.

        The "strike" command adds an additional strike to the given member, then performs the
        appropriate moderation action to the member, according to the new number of strikes.
        """
        member_id_not_integer_error: ValueError
        try:
            strike_member: discord.Member = await self.bot.get_member_from_str_id(
                str_strike_member_id,
            )
        except ValueError as member_id_not_integer_error:
            await self.command_send_error(ctx, message=member_id_not_integer_error.args[0])
            return

        await self._command_perform_strike(ctx, strike_member)

    @discord.slash_command(  # type: ignore[misc, no-untyped-call]
        name="get-strikes",
        description="Get the number of strikes a user has.",
    )
    @discord.option(  # type: ignore[misc, no-untyped-call]
        name="user",
        description="The user to check the number of strikes for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_strike_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_strikes(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", str_strike_member_id: str
    ) -> None:
        """
        Define method and callback response of of the "get-strikes" command.

        Responds with the number of strikes a user has.
        """
        try:
            strike_member: discord.Member = await self.bot.get_member_from_str_id(
                str_member_id=str_strike_member_id
            )
        except ValueError as member_id_not_integer_error:
            await self.command_send_error(ctx, message=member_id_not_integer_error.args[0])
            return

        strikes_count: int = 0
        try:
            strikes_count = (
                await DiscordMemberStrikes.objects.aget(discord_id=strike_member.id)
            ).strikes
        except DiscordMemberStrikes.DoesNotExist:
            logger.debug("No strikes found for user %s", strike_member)

        await ctx.respond(
            content=(f"User {strike_member.mention} has {strikes_count} strikes."),
            ephemeral=True,
        )

    @discord.slash_command(  # type: ignore[misc, no-untyped-call]
        name="decrement-strikes",
        description="Remove a single strike from a user.",
    )
    @discord.option(  # type: ignore[misc, no-untyped-call]
        name="user",
        description="The user to remove a strike from.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_strike_member_id",
    )
    async def decrement_strikes(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", str_strike_member_id: str
    ) -> None:
        """
        Definition & callback response of the "decrement-strikes" command.

        The "decrement-strikes" command removes a strike from the given member.
        If the member only has one strike, the corresponding `DiscordMemberStrikes`
        object will be deleted from the database.
        """
        try:
            strike_member: discord.Member = await self.bot.get_member_from_str_id(
                str_member_id=str_strike_member_id,
            )
        except ValueError as member_id_not_integer_error:
            await self.command_send_error(ctx, message=member_id_not_integer_error.args[0])
            return

        try:
            discord_member_strikes: DiscordMemberStrikes = (
                await DiscordMemberStrikes.objects.aget(discord_id=strike_member.id)
            )
        except DiscordMemberStrikes.DoesNotExist:
            await ctx.respond(
                content=(
                    ":information_source: No action taken. "
                    f"User {strike_member.mention} does not have any strikes to remove!"
                ),
                ephemeral=True,
            )
            logger.info(
                "%s attempted to remove a strike from user %s, but they had none",
                ctx.user,
                strike_member,
            )
            return

        if discord_member_strikes.strikes <= 1:
            await discord_member_strikes.adelete()
            await ctx.respond(
                content=f"Successfully removed all strikes from {strike_member.mention}.",
                ephemeral=True,
            )
            logger.info(
                "%s removed all strikes from user %s",
                ctx.user,
                strike_member,
            )
            return

        discord_member_strikes.strikes -= 1
        await discord_member_strikes.asave()
        await ctx.respond(
            content=(
                f"Successfully removed a strike from {strike_member.mention}. "
                f"User now has {discord_member_strikes.strikes} strikes."
            ),
            ephemeral=True,
        )
        logger.info(
            "%s removed 1 strike from user %s, they now have %s",
            ctx.user,
            strike_member,
            discord_member_strikes.strikes,
        )

    @discord.slash_command(  # type: ignore[misc, no-untyped-call]
        name="list-strikes",
        description="List all users with strikes.",
    )
    async def list_strikes(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc, no-untyped-call]
        """
        Definition & callback response of the "list-strikes" command.

        The "list-strikes" command lists all users with strikes.
        """
        strikes_counts: dict[str, int] = {
            str(strike.discord_member): strike.strikes
            async for strike in DiscordMemberStrikes.objects.select_related().all()
        }
        await ctx.respond(strikes_counts)


class StrikeContextCommandsCog(BaseStrikeCog):
    """Cog class that defines the context menu strike command and its call-back method."""

    async def _send_message_to_committee(
        self, ctx: "TeXBotApplicationContext", message: discord.Message
    ) -> None:
        """Send a provided message to committee channels."""
        discord_channel: discord.TextChannel | None = discord.utils.get(
            self.bot.main_guild.text_channels,
            name="discord",  # TODO: Make this user-configurable  # noqa: FIX002
        )

        if not discord_channel:
            await self.command_send_error(
                ctx=ctx,
                message="Could not find the `#discord` channel in the main guild!",
            )
            return

        if not message.guild:
            await self.command_send_error(
                ctx,
                message="Message supplied did not have a guild ID!",
            )
            return

        embed_content: str = ""

        if message.content:
            embed_content += message.content[:200]
            embed_content += "..."
        else:
            embed_content += "_Reported message had no content_"
            if len(message.attachments) > 0 or len(message.embeds) > 0:
                embed_content += " _but did have one or more attachments!_"

        embed_content += f"\n[View Original]({message.jump_url})"

        if message.reference:
            embed_content += f"\n[View Message this replied to]({message.reference.jump_url})"

        message_author_avatar_url: str | None = message.author.display_avatar.url

        embed_author: discord.EmbedAuthor = discord.EmbedAuthor(
            name=message.author.display_name,
            icon_url=message_author_avatar_url,
        )

        embed_image: str | None = None
        if len(message.attachments) == 1:
            attachment_type: str | None = message.attachments[0].content_type
            if attachment_type and "image" in attachment_type:
                embed_image = message.attachments[0].url

        await discord_channel.send(
            content=f"{ctx.user.mention} reported the following message:",
            embed=discord.Embed(
                author=embed_author,
                description=embed_content,
                colour=message.author.colour,
                image=embed_image,
            ),
        )

        await ctx.respond(
            content=":white_check_mark: Successfully reported message to committee channels!",
            ephemeral=True,
        )

    @discord.user_command(name="Strike User")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def user_strike(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", member: discord.Member
    ) -> None:
        """Call the _strike command, providing the required command arguments."""
        await self._command_perform_strike(ctx, member)

    @discord.message_command(name="Strike Message Author")  # type: ignore[no-untyped-call, misc]
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def strike_message_author(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", message: discord.Message
    ) -> None:
        """Call the _strike command on the message author."""
        strike_user: discord.Member = await self.bot.get_member_from_str_id(
            str(message.author.id),
        )
        await self._send_message_to_committee(ctx, message=message)
        await self._command_perform_strike(ctx, strike_member=strike_user)

    @discord.message_command(  # type: ignore[no-untyped-call, misc]
        name="Send Message to Committee",
        description="Sends the selected message to the committee channel for discussion.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def send_message_to_committee(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", message: discord.Message
    ) -> None:
        """Send a copy of the selected message to committee channels for review."""
        await self._send_message_to_committee(ctx, message=message)
