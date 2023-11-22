"""Contains cog classes for any send_get_roles_reminders interactions."""

import contextlib
import datetime
import functools
import logging
from typing import Final

import discord
from discord import AuditLogAction
from discord.ext import tasks

from cogs._utils import ErrorCaptureDecorators, TeXBotCog, capture_guild_does_not_exist_error
from config import settings
from db.core.models import SentGetRolesReminderMember
from exceptions import GuestRoleDoesNotExist, RolesChannelDoesNotExist
from utils import TeXBot


class SendGetRolesRemindersTaskCog(TeXBotCog):
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

    @tasks.loop(**settings["GET_ROLES_REMINDER_INTERVAL"])
    @functools.partial(
        ErrorCaptureDecorators.capture_error_and_close,
        error_type=GuestRoleDoesNotExist,
        close_func=ErrorCaptureDecorators.critical_error_close_func
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
        guild: discord.Guild = self.bot.css_guild
        guest_role: discord.Role = await self.bot.guest_role

        # noinspection PyUnusedLocal
        roles_channel_mention: str = "#roles"
        with contextlib.suppress(RolesChannelDoesNotExist):
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
                "Joint Honours"
                "Year In Industry",
                "Year Abroad",
                "PGT",
                "PGR",
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
                "Github",
                "Archivist",
                "News"
            }
        )

        member: discord.Member
        for member in guild.members:
            member_requires_opt_in_roles_reminder: bool = (
                not member.bot
                and guest_role in member.roles
                and not any(
                    opt_in_role_name in {role.name for role in member.roles}
                    for opt_in_role_name
                    in OPT_IN_ROLE_NAMES
                )
            )
            if not member_requires_opt_in_roles_reminder:
                continue

            hashed_member_id: str = SentGetRolesReminderMember.hash_member_id(member.id)
            sent_get_roles_reminder_member_exists: bool = (
                await SentGetRolesReminderMember.objects.filter(
                    hashed_member_id=hashed_member_id
                ).aexists()
            )
            if sent_get_roles_reminder_member_exists:
                continue

            try:
                # noinspection PyTypeChecker
                guest_role_received_time: datetime.datetime = await anext(
                    log.created_at
                    async for log
                    in guild.audit_logs(action=AuditLogAction.member_role_update)
                    if (
                        log.target == member
                        and guest_role not in log.before.roles
                        and guest_role in log.after.roles
                    )
                )
            except StopIteration:
                logging.error(
                    (
                        "Member with ID: %s could not be checked whether to send "
                        "role_reminder, because their \"guest_role_received_time\" "
                        "could not be found."
                    ),
                    member.id
                )
                continue

            time_since_role_received: datetime.timedelta = (
                    discord.utils.utcnow() - guest_role_received_time
            )
            if time_since_role_received <= datetime.timedelta(days=1):
                continue

            await member.send(
                "Hey! It seems like you joined the CSS Discord server and have been "
                "given the `@Guest` role but have not yet nabbed yourself any "
                f"opt-in roles.\nYou can head to {roles_channel_mention} "
                "and click on the icons to get optional roles like pronouns "
                "and year group identifiers."
            )

            await SentGetRolesReminderMember.objects.acreate(
                hashed_member_id=hashed_member_id
            )

    @send_get_roles_reminders.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
