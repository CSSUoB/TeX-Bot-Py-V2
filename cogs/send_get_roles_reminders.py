"""Contains cog classes for any send_get_roles_reminders interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("SendGetRolesRemindersTaskCog",)


import contextlib
import functools
import logging
from logging import Logger
from typing import TYPE_CHECKING, Final

import discord
from discord import AuditLogAction
from discord.ext import tasks

import utils
from config import settings
from db.core.models import SentGetRolesReminderMember
from exceptions import GuestRoleDoesNotExistError, RolesChannelDoesNotExistError
from utils import TeXBot, TeXBotBaseCog
from utils.error_capture_decorators import (
    ErrorCaptureDecorators,
    capture_guild_does_not_exist_error,
)

if TYPE_CHECKING:
    import datetime

logger: Logger = logging.getLogger("TeX-Bot")


class SendGetRolesRemindersTaskCog(TeXBotBaseCog):
    """Cog class that defines the send_get_roles_reminders task."""

    def __init__(self, bot: TeXBot) -> None:
        """Start all task managers when this cog is initialised."""
        if settings["SEND_GET_ROLES_REMINDERS"]:
            self.send_get_roles_reminders.start()

        super().__init__(bot)

    def cog_unload(self) -> None:
        """
        Unload hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.send_get_roles_reminders.cancel()

    @tasks.loop(**settings["ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL"])  # type: ignore[misc]
    @functools.partial(
        ErrorCaptureDecorators.capture_error_and_close,
        error_type=GuestRoleDoesNotExistError,
        close_func=ErrorCaptureDecorators.critical_error_close_func,
    )
    @capture_guild_does_not_exist_error
    async def send_get_roles_reminders(self) -> None:
        """
        Recurring task to send an opt-in roles reminder message to Discord members' DMs.

        The opt-in reminder message suggests that the Discord member has not given themselves
        any of the optional opt-in roles.

        See README.md for the full list of conditions for when these
        reminders are sent.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        guild: discord.Guild = self.bot.main_guild
        guest_role: discord.Role = await self.bot.guest_role

        # noinspection PyUnusedLocal
        roles_channel_mention: str = "#roles"
        with contextlib.suppress(RolesChannelDoesNotExistError):
            roles_channel_mention = (await self.bot.roles_channel).mention

        # noinspection SpellCheckingInspection
        OPT_IN_ROLE_NAMES: Final[frozenset[str]] = frozenset(
            {
                "He / Him",
                "She / Her",
                "They / Them",
                "Neopronouns",
                "Foundation Year",
                "First Year",
                "Second Year",
                "Final Year",
                "Year In Industry",
                "Year Abroad",
                "PGT",
                "PGR",
                "Joint Honours",
                "Alumnus/Alumna",
                "Postdoc",
                "Serious Talk",
                "Housing",
                "Gaming",
                "Anime",
                "Sport",
                "Food",
                "Industry",
                "Minecraft",
                "GitHub",
                "Archivist",
                "Rate My Meal",
                "Website",
                "Student Rep",
            },
        )

        member: discord.Member
        for member in guild.members:
            member_requires_opt_in_roles_reminder: bool = (
                not member.bot
                and utils.is_member_inducted(member)
                and not any(
                    opt_in_role_name.lower() in {role.name.lower() for role in member.roles}
                    for opt_in_role_name
                    in OPT_IN_ROLE_NAMES
                )
            )
            if not member_requires_opt_in_roles_reminder:
                continue

            sent_get_roles_reminder_member_exists: bool = (
                await (
                    await SentGetRolesReminderMember.objects.afilter(discord_id=member.id)
                ).aexists()
            )
            if sent_get_roles_reminder_member_exists:
                continue

            # noinspection PyUnusedLocal
            guest_role_received_time: datetime.datetime | None = None
            with contextlib.suppress(StopIteration, StopAsyncIteration):
                # noinspection PyTypeChecker
                guest_role_received_time = await anext(
                    log.created_at
                    async for log
                    in guild.audit_logs(action=AuditLogAction.member_role_update)
                    if (
                        log.target == member
                        and guest_role not in log.before.roles
                        and guest_role in log.after.roles
                    )
                )

            if guest_role_received_time is not None:
                time_since_role_received: datetime.timedelta = (
                    discord.utils.utcnow() - guest_role_received_time
                )
                if time_since_role_received <= settings["SEND_GET_ROLES_REMINDERS_DELAY"]:
                    continue

            if member not in guild.members:  # HACK: Caching errors can cause the member to no longer be part of the guild at this point, so this check must be performed before sending that member a message # noqa: FIX004
                logger.info(
                    (
                        "Member with ID: %s does not need to be sent a reminder "
                        "because they have left the server."
                    ),
                    member.id,
                )
                continue

            try:
                await member.send(
                    "Hey! It seems like you have been given the `@Guest` role "
                    f"on the {self.bot.group_short_name} Discord server "
                    " but have not yet nabbed yourself any opt-in roles.\n"
                    f"You can head to {roles_channel_mention} "
                    "and click on the icons to get optional roles like pronouns "
                    "and year group identifiers.",
                )
            except discord.Forbidden:
                logger.warning("Failed to open DM channel to %s so no reminder was sent.", member)

            await SentGetRolesReminderMember.objects.acreate(discord_id=member.id)

    @send_get_roles_reminders.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
