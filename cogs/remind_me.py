"""Contains cog classes for any remind_me interactions."""

import datetime
import functools
import itertools
import logging
import re
from typing import TYPE_CHECKING, override

import discord
import parsedatetime
from discord.ext import tasks
from django.core.exceptions import ValidationError
from django.utils import timezone

from db.core.models import DiscordMember, DiscordReminder
from utils import TeXBotBaseCog

if TYPE_CHECKING:
    import time
    from collections.abc import Iterator, Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBot, TeXBotApplicationContext, TeXBotAutocompleteContext

__all__: "Sequence[str]" = ("ClearRemindersBacklogTaskCog", "RemindMeCommandCog")


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class RemindMeCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/remind-me" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_delays(  # noqa: PLR0912, PLR0915
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the common delay input values.

        The delay entered by a member in the "remind_me" slash-command must be within this set
        of common delay input values.
        """
        if not ctx.value:
            return {
                "in 5 minutes",
                "1 hours time",
                "1min",
                "30 secs",
                "2 days time",
                "22/9/2040",
                "5h",
            }

        SECONDS_CHOICES: Final[frozenset[str]] = frozenset({"s", "sec", "second"})
        MINUTES_CHOICES: Final[frozenset[str]] = frozenset({"m", "min", "minute"})
        HOURS_CHOICES: Final[frozenset[str]] = frozenset({"h", "hr", "hour"})
        DAYS_CHOICES: Final[frozenset[str]] = frozenset({"d", "dy", "day"})
        WEEKS_CHOICES: Final[frozenset[str]] = frozenset({"w", "wk", "week"})
        YEARS_CHOICES: Final[frozenset[str]] = frozenset({"y", "yr", "year"})
        TIME_CHOICES: Final[frozenset[str]] = (
            SECONDS_CHOICES
            | MINUTES_CHOICES
            | HOURS_CHOICES
            | DAYS_CHOICES
            | WEEKS_CHOICES
            | YEARS_CHOICES
        )

        delay_choices: set[str] = set()

        if re.fullmatch(r"\Ain? ?\Z", ctx.value):
            FORMATTED_TIME_NUMS: Final[Iterator[tuple[int, str, str]]] = itertools.product(
                range(1, 150), {"", " "}, {"", "s"}
            )
            time_num: int
            joiner: str
            has_s: str
            for time_num, joiner, has_s in FORMATTED_TIME_NUMS:
                delay_choices.update(
                    f"{time_num}{joiner}{time_choice}{has_s}"
                    for time_choice in TIME_CHOICES
                    if not (len(time_choice) <= 1 and has_s)
                )

            return {f"in {delay_choice}" for delay_choice in delay_choices}

        match: re.Match[str] | None
        if match := re.fullmatch(r"\Ain (?P<partial_date>\d{0,3})\Z", ctx.value):
            for joiner, has_s in itertools.product({"", " "}, {"", "s"}):
                delay_choices.update(
                    f"""{match.group("partial_date")}{joiner}{time_choice}{has_s}"""
                    for time_choice in TIME_CHOICES
                    if not (len(time_choice) <= 1 and has_s)
                )

            return {f"in {delay_choice}" for delay_choice in delay_choices}

        current_year: int = discord.utils.utcnow().year

        if re.fullmatch(r"\A\d{1,3}\Z", ctx.value):
            for joiner, has_s in itertools.product({"", " "}, {"", "s"}):
                delay_choices.update(
                    f"{joiner}{time_choice}{has_s}"
                    for time_choice in TIME_CHOICES
                    if not (len(time_choice) <= 1 and has_s)
                )

            if 1 <= int(ctx.value) <= 31:
                FORMATTED_DAY_DATE_CHOICES: Final[Iterator[tuple[int, int, str]]] = (
                    itertools.product(
                        range(1, 12),
                        range(current_year, current_year + 40),
                        ("/", " / ", "-", " - ", ".", " . "),
                    )
                )
                month: int
                year: int
                for month, year, joiner in FORMATTED_DAY_DATE_CHOICES:
                    delay_choices.add(f"{joiner}{month}{joiner}{year}")
                    if month < 10:
                        delay_choices.add(f"{joiner}0{month}{joiner}{year}")

        elif match := re.fullmatch(r"\A\d{1,3}(?P<ctx_time_choice> ?[A-Za-z]*)\Z", ctx.value):
            FORMATTED_TIME_CHOICES: Final[Iterator[tuple[str, str, str]]] = itertools.product(
                {"", " "}, TIME_CHOICES, {"", "s"}
            )
            time_choice: str
            for joiner, time_choice, has_s in FORMATTED_TIME_CHOICES:
                if has_s and len(time_choice) <= 1:
                    continue

                formatted_time_choice: str = joiner + time_choice + has_s

                slice_size: int
                for slice_size in range(1, len(formatted_time_choice) + 1):
                    if (
                        match.group("ctx_time_choice").casefold()
                        == formatted_time_choice[:slice_size]
                    ):
                        delay_choices.add(formatted_time_choice[slice_size:])

        elif match := re.fullmatch(r"\A(?P<date>\d{1,2}) ?[/\-.] ?\Z", ctx.value):
            if 1 <= int(match.group("date")) <= 31:
                FORMATTED_DAY_AND_JOINER_DATE_CHOICES: Final[
                    Iterator[tuple[int, int, str]]
                ] = itertools.product(
                    range(1, 12),
                    range(current_year, current_year + 40),
                    ("/", " / ", "-", " - ", ".", " . "),
                )
                for month, year, joiner in FORMATTED_DAY_AND_JOINER_DATE_CHOICES:
                    delay_choices.add(f"{month}{joiner}{year}")
                    if month < 10:
                        delay_choices.add(f"0{month}{joiner}{year}")

        elif match := re.fullmatch(
            r"\A(?P<date>\d{1,2}) ?[/\-.] ?(?P<month>\d{1,2})\Z", ctx.value
        ):
            if 1 <= int(match.group("date")) <= 31 and 1 <= int(match.group("month")) <= 12:
                for year in range(current_year, current_year + 40):
                    for joiner in ("/", " / ", "-", " - ", ".", " . "):
                        delay_choices.add(f"{joiner}{year}")

        elif match := re.fullmatch(
            r"\A(?P<date>\d{1,2}) ?[/\-.] ?(?P<month>\d{1,2}) ?[/\-.] ?\Z", ctx.value
        ):
            if 1 <= int(match.group("date")) <= 31 and 1 <= int(match.group("month")) <= 12:
                for year in range(current_year, current_year + 40):
                    delay_choices.add(f"{year}")

        elif match := re.fullmatch(
            (
                r"\A(?P<date>\d{1,2}) ?[/\-.] ?"
                r"(?P<month>\d{1,2}) ?[/\-.] ?"
                r"(?P<partial_year>\d{1,3})\Z"
            ),
            ctx.value,
        ):
            if 1 <= int(match.group("date")) <= 31 and 1 <= int(match.group("month")) <= 12:
                for year in range(current_year, current_year + 40):
                    delay_choices.add(f"{year}"[len(match.group("partial_year")) :])

        return {f"{ctx.value}{delay_choice}".casefold() for delay_choice in delay_choices}

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="remind-me",
        description="Responds with the given message after the specified time.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="delay",
        input_type=str,
        description="The amount of time to wait before reminding you.",
        required=True,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_delays),  # type: ignore[arg-type]
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="message",
        input_type=str,
        description="The message you want to be reminded with.",
        required=False,
    )
    async def remind_me(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", delay: str, message: str
    ) -> None:
        """
        Definition & callback response of the "remind_me" command.

        The "remind_me" command responds with the given message after the specified time.
        """
        parsed_time: tuple[time.struct_time, int] = parsedatetime.Calendar().parseDT(
            delay, tzinfo=timezone.get_current_timezone()
        )

        if parsed_time[1] == 0:
            await self.command_send_error(
                ctx,
                message=f"The value provided in the {'delay'!r} argument was not a time/date.",
            )
            return

        if message:
            message = re.sub(r"<@[&#]?\d+>", "@...", message.strip())

        try:
            reminder: DiscordReminder = await DiscordReminder.objects.acreate(  # type: ignore[misc]
                discord_member=(
                    await DiscordMember.objects.aget_or_create(discord_id=ctx.user.id)
                )[0],
                message=message or "",
                channel_id=ctx.channel_id,
                send_datetime=parsed_time[0],
                channel_type=ctx.channel.type,
            )
        except ValidationError as create_discord_reminder_error:
            ERROR_IS_ALREADY_EXISTS: Final[bool] = bool(
                "__all__" in create_discord_reminder_error.message_dict
                and any(
                    "already exists" in error
                    for error in create_discord_reminder_error.message_dict["__all__"]
                )
            )
            if not ERROR_IS_ALREADY_EXISTS:
                await self.command_send_error(ctx, message="An unrecoverable error occurred.")
                logger.critical(
                    "Error when creating DiscordReminder object: %s",
                    create_discord_reminder_error,
                )
                await self.bot.close()

            await self.command_send_error(
                ctx, message="You already have a reminder with that message in this channel!"
            )
            return

        await ctx.respond("Reminder set!", ephemeral=True)

        await discord.utils.sleep_until(reminder.send_datetime)

        user_mention: str | None = None
        if ctx.guild:
            user_mention = ctx.user.mention

        await ctx.send_followup(reminder.get_formatted_message(user_mention))

        await reminder.adelete()


class ClearRemindersBacklogTaskCog(TeXBotBaseCog):
    """Cog class that defines the clear_reminders_backlog task."""

    @override
    def __init__(self, bot: "TeXBot") -> None:
        """Start all task managers when this cog is initialised."""
        _ = self.clear_reminders_backlog.start()

        super().__init__(bot)

    @override
    def cog_unload(self) -> None:
        """
        Unload-hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.clear_reminders_backlog.cancel()

    @tasks.loop(minutes=15)
    async def clear_reminders_backlog(self) -> None:
        """Recurring task to send any late Discord reminders still stored in the database."""
        TEXTABLE_CHANNEL_TYPES: Final[frozenset[discord.ChannelType]] = frozenset(
            {
                discord.ChannelType.text,
                discord.ChannelType.group,
                discord.ChannelType.public_thread,
                discord.ChannelType.private_thread,
            }
        )

        reminder: DiscordReminder
        async for reminder in DiscordReminder.objects.select_related("discord_member").all():
            time_since_reminder_needed_to_be_sent: datetime.timedelta = (
                discord.utils.utcnow() - reminder.send_datetime
            )
            if time_since_reminder_needed_to_be_sent > datetime.timedelta(minutes=15):
                user: discord.User | None = discord.utils.find(
                    functools.partial(
                        lambda _user, _reminder: (
                            not _user.bot and _user.id == _reminder.discord_member.discord_id
                        ),
                        _reminder=reminder,
                    ),
                    self.bot.users,
                )

                if not user:
                    logger.warning(
                        "User with ID: %s no longer exists.",
                        reminder.discord_member.discord_id,
                    )
                    await reminder.adelete()
                    continue

                channel: discord.PartialMessageable = self.bot.get_partial_messageable(
                    reminder.channel_id, type=reminder.channel_type
                )

                user_mention: str | None = None
                if channel.type in TEXTABLE_CHANNEL_TYPES:
                    user_mention = user.mention

                elif channel.type != discord.ChannelType.private:
                    logger.critical(
                        ValueError(
                            "Reminder's channel_id must refer to a valid text channel/DM."
                        )
                    )
                    await self.bot.close()

                await channel.send(
                    "**Sorry it's a bit late! "
                    "(I'm just catching up with some reminders I missed!)**\n\n"
                    f"{reminder.get_formatted_message(user_mention)}"
                )

                await reminder.adelete()

    @clear_reminders_backlog.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
