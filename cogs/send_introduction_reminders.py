"""Contains cog classes for any send_introduction_reminders interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("SendIntroductionRemindersTaskCog",)


import datetime
import functools
import logging
from logging import Logger
from typing import Final

import discord
import emoji
from discord import ui
from discord.ext import tasks
from discord.ui import View
from django.core.exceptions import ValidationError

from config import settings
from db.core.models import (
    IntroductionReminderOptOutMember,
    SentOneOffIntroductionReminderMember,
)
from exceptions import DiscordMemberNotInMainGuildError, GuestRoleDoesNotExistError
from utils import TeXBot, TeXBotBaseCog
from utils.error_capture_decorators import (
    ErrorCaptureDecorators,
    capture_guild_does_not_exist_error,
)

logger: Logger = logging.getLogger("TeX-Bot")


class SendIntroductionRemindersTaskCog(TeXBotBaseCog):
    """Cog class that defines the send_introduction_reminders task."""

    def __init__(self, bot: TeXBot) -> None:
        """Start all task managers when this cog is initialised."""
        if settings["SEND_INTRODUCTION_REMINDERS"]:
            if settings["SEND_INTRODUCTION_REMINDERS"] == "interval":
                SentOneOffIntroductionReminderMember.objects.all().delete()

            self.send_introduction_reminders.start()

        super().__init__(bot)

    def cog_unload(self) -> None:
        """
        Unload hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.send_introduction_reminders.cancel()

    @TeXBotBaseCog.listener()
    async def on_ready(self) -> None:
        """Add OptOutIntroductionRemindersView to the bot's list of permanent views."""
        self.bot.add_view(
            self.OptOutIntroductionRemindersView(self.bot),
        )

    @tasks.loop(**settings["SEND_INTRODUCTION_REMINDERS_INTERVAL"])  # type: ignore[misc]
    @functools.partial(
        ErrorCaptureDecorators.capture_error_and_close,
        error_type=GuestRoleDoesNotExistError,
        close_func=ErrorCaptureDecorators.critical_error_close_func,
    )
    @capture_guild_does_not_exist_error
    async def send_introduction_reminders(self) -> None:
        """
        Recurring task to send an introduction reminder message to Discord members' DMs.

        The introduction reminder suggests that the Discord member should send a message to
        introduce themselves to your group's Discord guild.

        See README.md for the full list of conditions for when these
        reminders are sent.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        guild: discord.Guild = self.bot.main_guild

        member: discord.Member
        for member in guild.members:
            if self.bot.is_member_inducted(member) or member.bot:
                continue

            if not member.joined_at:
                logger.error(
                    (
                        "Member with ID: %s could not be checked whether to send "
                        "introduction_reminder, because their %s attribute "
                        "was None."
                    ),
                    member.id,
                    repr("joined_at"),
                )
                continue

            member_needs_one_off_reminder: bool = (
                settings["SEND_INTRODUCTION_REMINDERS"] == "once"
                and not await SentOneOffIntroductionReminderMember.objects.filter(
                    hashed_member_id=SentOneOffIntroductionReminderMember.hash_member_id(
                        member.id,
                    ),
                ).aexists()
            )
            member_needs_recurring_reminder: bool = (
                    settings["SEND_INTRODUCTION_REMINDERS"] == "interval"
            )
            member_recently_joined: bool = (discord.utils.utcnow() - member.joined_at) <= max(
                settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY"] / 3,
                datetime.timedelta(days=1),
            )
            member_opted_out_from_reminders: bool = await IntroductionReminderOptOutMember.objects.filter(  # noqa: E501
                hashed_member_id=IntroductionReminderOptOutMember.hash_member_id(member.id),
            ).aexists()
            member_needs_reminder: bool = (
                    (member_needs_one_off_reminder or member_needs_recurring_reminder)
                    and not member_recently_joined
                    and not member_opted_out_from_reminders
            )

            if member_needs_reminder:
                async for message in member.history():
                    # noinspection PyUnresolvedReferences
                    message_contains_opt_in_out_button: bool = (
                        bool(message.components)
                        and isinstance(message.components[0], discord.ActionRow)
                        and isinstance(message.components[0].children[0], discord.Button)
                        and message.components[0].children[0].custom_id == "opt_out_introduction_reminders_button"  # noqa: E501
                    )
                    if message_contains_opt_in_out_button:
                        await message.edit(view=None)

                if member not in guild.members:  # HACK: Caching errors can cause the member to no longer be part of the guild at this point, so this check must be performed before sending that member a message # noqa: FIX004
                    logger.info(
                        (
                            "Member with ID: %s does not need to be sent a reminder "
                            "because they have left the server."
                        ),
                        member.id,
                    )
                    continue

                await member.send(
                    content=(
                        "Hey! It seems like you joined "
                        f"the {self.bot.group_short_name} Discord server "
                        "but have not yet introduced yourself.\n"
                        "You will only get access to the rest of the server after sending "
                        "an introduction message."
                    ),
                    view=(
                        self.OptOutIntroductionRemindersView(self.bot)
                        if settings["SEND_INTRODUCTION_REMINDERS"] == "interval"
                        else None  # type: ignore[arg-type]
                    ),
                )

                await SentOneOffIntroductionReminderMember.objects.acreate(
                        member_id=member.id,
                    )


    class OptOutIntroductionRemindersView(View):
        """
        A discord.View containing a button to opt-in/out of introduction reminders.

        This discord.View contains a single button that can change the state of whether the
        member will be sent reminders to send an introduction message in
        your group's Discord guild.
        The view object will be sent to the member's DMs, after a delay period after
        joining your group's Discord guild.
        """

        def __init__(self, bot: TeXBot) -> None:
            """Initialize a new discord.View, to opt-in/out of introduction reminders."""
            self.bot: TeXBot = bot

            super().__init__(timeout=None)

        async def send_error(self, interaction: discord.Interaction, error_code: str | None = None, message: str | None = None, logging_message: str | BaseException | None = None) -> None:  # noqa: E501
            """
            Construct & format an error message from the given details.

            The constructed error message is then sent as the response
            to the given interaction.
            """
            await TeXBotBaseCog.send_error(
                self.bot,
                interaction,
                interaction_name="opt_out_introduction_reminders",
                error_code=error_code,
                message=message,
                logging_message=logging_message,
            )

        @ui.button(  # type: ignore[misc]
            label="Opt-out of introduction reminders",
            custom_id="opt_out_introduction_reminders_button",
            style=discord.ButtonStyle.red,
            emoji=discord.PartialEmoji.from_str(
                emoji.emojize(":no_good:", language="alias"),
            ),
        )
        async def opt_out_introduction_reminders_button_callback(self, button: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
            """
            Set the opt-in/out flag depending on the status of the button.

            This function is attached as a button's callback, so will run whenever the button
            is pressed.
            """
            BUTTON_WILL_MAKE_OPT_OUT: Final[bool] = bool(
                button.style == discord.ButtonStyle.red
                or str(button.emoji) == emoji.emojize(":no_good:", language="alias")
                or (button.label and "Opt-out" in button.label),
            )

            _BUTTON_WILL_MAKE_OPT_IN: Final[bool] = bool(
                    button.style == discord.ButtonStyle.green
                    or str(button.emoji) == emoji.emojize(
                        ":raised_hand:",
                        language="alias",
                    )
                    or button.label and "Opt back in" in button.label)
            INCOMPATIBLE_BUTTONS: Final[bool] = bool(
                (BUTTON_WILL_MAKE_OPT_OUT and _BUTTON_WILL_MAKE_OPT_IN)
                or (not BUTTON_WILL_MAKE_OPT_OUT and not _BUTTON_WILL_MAKE_OPT_IN),
            )
            if INCOMPATIBLE_BUTTONS:
                INCOMPATIBLE_BUTTONS_MESSAGE: Final[str] = "Conflicting buttons pressed"
                raise ValueError(INCOMPATIBLE_BUTTONS_MESSAGE)

            if not interaction.user:
                await self.send_error(interaction)
                return

            try:
                interaction_member: discord.Member = await self.bot.get_main_guild_member(
                    interaction.user,
                )
            except DiscordMemberNotInMainGuildError:
                await self.send_error(
                    interaction,
                    message=(
                        f"You must be a member "
                        f"of the {self.bot.group_short_name} Discord server "
                        f"""to opt{
                            "-out of" if BUTTON_WILL_MAKE_OPT_OUT else " back in to"
                        } introduction reminders."""
                    ),
                )
                return

            if BUTTON_WILL_MAKE_OPT_OUT:
                try:
                    await IntroductionReminderOptOutMember.objects.acreate(
                        member_id=interaction_member.id,
                    )
                except ValidationError as create_introduction_reminder_opt_out_member_error:
                    error_is_already_exists: bool = (
                        "hashed_member_id" in create_introduction_reminder_opt_out_member_error.message_dict  # noqa: E501
                        and any(
                            "already exists" in error
                            for error
                            in create_introduction_reminder_opt_out_member_error.message_dict[
                                "hashed_member_id"
                            ]
                        )
                    )
                    if not error_is_already_exists:
                        raise

                button.style = discord.ButtonStyle.green
                button.label = "Opt back in to introduction reminders"
                button.emoji = discord.PartialEmoji.from_str(
                    emoji.emojize(":raised_hand:", language="alias"),
                )

                await interaction.response.edit_message(view=self)

            else:
                try:
                    introduction_reminder_opt_out_member: IntroductionReminderOptOutMember = await IntroductionReminderOptOutMember.objects.aget(  # noqa: E501
                        hashed_member_id=IntroductionReminderOptOutMember.hash_member_id(
                            interaction_member.id,
                        ),
                    )
                except IntroductionReminderOptOutMember.DoesNotExist:
                    pass
                else:
                    await introduction_reminder_opt_out_member.adelete()

                button.style = discord.ButtonStyle.red
                button.label = "Opt-out of introduction reminders"
                button.emoji = discord.PartialEmoji.from_str(
                    emoji.emojize(":no_good:", language="alias"),
                )

                await interaction.response.edit_message(view=self)

    @send_introduction_reminders.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
