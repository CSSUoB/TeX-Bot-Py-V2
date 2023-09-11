"""
Contains repeating tasks that are executed at set intervals.

(E.g. database cleanup or sending message reminders to members' DMs).
"""

import datetime
import logging
from typing import Final

import discord
import emoji
from discord import AuditLogAction, ui
from discord.ext import tasks
from discord.ui import View
from django.core.exceptions import ValidationError

from cogs.utils import TeXBotCog
from config import settings
from db.core.models import (
    DiscordReminder,
    IntroductionReminderOptOutMember,
    SentGetRolesReminderMember,
    SentOneOffIntroductionReminderMember,
)
from exceptions import GuestRoleDoesNotExist, GuildDoesNotExist
from utils import TeXBot

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


class TasksCog(TeXBotCog):
    """Cog container class that defines & initialises all recurring tasks."""

    def __init__(self, bot: TeXBot) -> None:
        """Start all task managers when this cog is initialised."""
        if settings["SEND_INTRODUCTION_REMINDERS"]:
            if settings["SEND_INTRODUCTION_REMINDERS"] == "interval":
                SentOneOffIntroductionReminderMember.objects.all().delete()

            self.introduction_reminder.start()

        if settings["KICK_NO_INTRODUCTION_MEMBERS"]:
            self.kick_no_introduction_members.start()

        self.clear_reminder_backlog.start()

        if settings["SEND_GET_ROLES_REMINDERS"]:
            self.get_roles_reminder.start()

        super().__init__(bot)

    def cog_unload(self) -> None:
        """
        Unload hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.introduction_reminder.cancel()
        self.kick_no_introduction_members.cancel()
        self.clear_reminder_backlog.cancel()
        self.get_roles_reminder.cancel()

    @tasks.loop(minutes=15)
    async def clear_reminder_backlog(self) -> None:
        """Recurring task to send any late Discord reminders still stored in the database."""
        TEXTABLE_CHANNEL_TYPES: Final[frozenset[discord.ChannelType]] = frozenset(
            {
                discord.ChannelType.text,
                discord.ChannelType.group,
                discord.ChannelType.public_thread,
                discord.ChannelType.private_thread
            }
        )

        reminder: DiscordReminder
        async for reminder in DiscordReminder.objects.all():
            time_since_reminder_needed_to_be_sent: datetime.timedelta = (
                    discord.utils.utcnow() - reminder.send_datetime
            )
            if time_since_reminder_needed_to_be_sent > datetime.timedelta(minutes=15):
                user: discord.User | None = discord.utils.find(
                    lambda u: (
                        not u.bot
                        and DiscordReminder.hash_member_id(u.id) == reminder.hashed_member_id
                    ),
                    self.bot.users
                )

                if not user:
                    logging.warning(
                        f"User with hashed user ID: {reminder.hashed_member_id}"
                        " no longer exists."
                    )
                    await reminder.adelete()
                    continue

                channel: discord.PartialMessageable = self.bot.get_partial_messageable(
                    reminder.channel_id,
                    type=(
                        discord.ChannelType(reminder.channel_type)
                        if reminder.channel_type
                        else None
                    )
                )

                user_mention: str | None = None
                if channel.type in TEXTABLE_CHANNEL_TYPES:
                    user_mention = user.mention

                elif channel.type != discord.ChannelType.private:
                    logging.critical(
                        ValueError(
                            "Reminder's channel_id must refer to a valid text channel/DM."
                        )
                    )
                    await self.bot.close()
                    return

                await channel.send(
                    "**Sorry it's a bit late!"
                    " (I'm just catching up with some reminders I missed!)**"
                    f"\n\n{reminder.get_formatted_message(user_mention)}"
                )

                await reminder.adelete()

    @tasks.loop(hours=24)
    async def kick_no_introduction_members(self) -> None:
        """
        Recurring task to kick any Discord members that have not introduced themselves.

        Other prerequisites must be met for this task to be activated, see README.md for the
        full list of conditions.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        guest_role: discord.Role | None = await self.bot.guest_role
        if not guest_role:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        member: discord.Member
        for member in guild.members:
            if guest_role in member.roles or member.bot:
                continue

            if not member.joined_at:
                logging.error(
                    f"Member with ID: {member.id} could not be checked whether to kick,"
                    " because their \"joined_at\" attribute was None."
                )
                continue

            kick_no_introduction_members_delay: datetime.timedelta = settings[
                "KICK_NO_INTRODUCTION_MEMBERS_DELAY"
            ]
            time_since_joining: datetime.timedelta = discord.utils.utcnow() - member.joined_at

            if time_since_joining > kick_no_introduction_members_delay:
                try:
                    await member.kick(
                        reason=(
                            "Member was in server without introduction sent"
                            f" for longer than {kick_no_introduction_members_delay}"
                        )
                    )
                except discord.Forbidden as kick_error:
                    logging.error(
                        f"Member with ID: {member.id} could not be kicked"
                        f" due to {kick_error.text}"
                    )

    @tasks.loop(**settings["INTRODUCTION_REMINDER_INTERVAL"])
    async def introduction_reminder(self) -> None:
        """
        Recurring task to send an introduction reminder message to Discord members' DMs.

        The introduction reminder suggests that the Discord member should send a message to
        introduce themselves to the CSS Discord server.

        See README.md for the full list of conditions for when these
        reminders are sent.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        guest_role: discord.Role | None = await self.bot.guest_role
        if not guest_role:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        member: discord.Member
        for member in guild.members:
            if guest_role in member.roles or member.bot:
                continue

            if not member.joined_at:
                logging.error(
                    f"Member with ID: {member.id} could not be checked whether to send"
                    " introduction_reminder, because their \"joined_at\" attribute was None."
                )
                continue

            member_needs_one_off_reminder: bool = (
                settings["SEND_INTRODUCTION_REMINDERS"] == "once"
                and not await SentOneOffIntroductionReminderMember.objects.filter(
                    hashed_member_id=SentOneOffIntroductionReminderMember.hash_member_id(
                        member.id
                    )
                ).aexists()
            )
            member_needs_recurring_reminder: bool = settings["SEND_INTRODUCTION_REMINDERS"] == "interval"  # noqa: E501
            member_recently_joined: bool = (discord.utils.utcnow() - member.joined_at) <= max(
                settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] / 3,
                datetime.timedelta(days=1)
            )
            member_opted_out_from_reminders: bool = await IntroductionReminderOptOutMember.objects.filter(  # noqa: E501
                hashed_member_id=IntroductionReminderOptOutMember.hash_member_id(member.id)
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

                await member.send(
                    content="Hey! It seems like you joined the CSS Discord server"
                            " but have not yet introduced yourself.\nYou will only get access"
                            " to the rest of the server after sending"
                            " an introduction message.",
                    view=(
                        self.OptOutIntroductionRemindersView(self.bot)
                        if settings["SEND_INTRODUCTION_REMINDERS"] == "interval"
                        else None  # type: ignore[arg-type]
                    )
                )

                await SentOneOffIntroductionReminderMember.objects.acreate(member_id=member.id)

    class OptOutIntroductionRemindersView(View):
        """
        A discord.View containing a button to opt-in/out of introduction reminders.

        This discord.View contains a single button that can change the state of whether the
        member will be sent reminders to send an introduction message in the
        CSS Discord server.
        The view object will be sent to the member's DMs, after a delay period after
        joining the CSS Discord server.
        """

        def __init__(self, bot: TeXBot):
            """Initialize a new discord.View, to opt-in/out of introduction reminders."""
            self.bot: TeXBot = bot

            super().__init__(timeout=None)

        @ui.button(
            label="Opt-out of introduction reminders",
            custom_id="opt_out_introduction_reminders_button",
            style=discord.ButtonStyle.red,
            emoji=discord.PartialEmoji.from_str(
                emoji.emojize(":no_good:", language="alias")
            )
        )
        async def opt_out_introduction_reminders_button_callback(self, button: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
            """
            Set the opt-in/out flag depending on the status of the button.

            This function is attached as a button's callback, so will run whenever the button
            is pressed.
            """
            try:
                guild: discord.Guild = self.bot.css_guild
            except GuildDoesNotExist as guild_error:
                logging.critical(guild_error)
                await self.bot.close()
                return

            if not interaction.user:
                await interaction.response.send_message(
                    ":warning:There was an error when trying to opt-in/out of"
                    " introduction reminders.:warning:",
                    ephemeral=True
                )
                return

            interaction_member: discord.Member | None = guild.get_member(interaction.user.id)

            button_will_make_opt_out: bool = (
                button.style == discord.ButtonStyle.red
                or str(button.emoji) == emoji.emojize(":no_good:", language="alias")
                or bool(button.label and "Opt-out" in button.label)
            )
            button_will_make_opt_in: bool = (
                button.style == discord.ButtonStyle.green
                or str(button.emoji) == emoji.emojize(":raised_hand:", language="alias")
                or bool(button.label and "Opt back in" in button.label)
            )

            if button_will_make_opt_out:
                if not interaction_member:
                    await interaction.response.send_message(
                        ":warning:There was an error when trying to opt-out of"
                        " introduction reminders.:warning:\n`You must be a member of"
                        " the CSS Discord server to opt-out of introduction reminders.`",
                        ephemeral=True
                    )
                    return

                try:
                    await IntroductionReminderOptOutMember.objects.acreate(
                        member_id=interaction_member.id
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
                    emoji.emojize(":raised_hand:", language="alias")
                )

                await interaction.response.edit_message(view=self)

            elif button_will_make_opt_in:
                if not interaction_member:
                    await interaction.response.send_message(
                        ":warning:There was an error when trying to opt back in"
                        " to introduction reminders.:warning:\n`You must be a member of"
                        " the CSS Discord server to opt back in to introduction reminders.`",
                        ephemeral=True
                    )
                    return

                try:
                    introduction_reminder_opt_out_member: IntroductionReminderOptOutMember = await IntroductionReminderOptOutMember.objects.aget(  # noqa: E501
                        hashed_member_id=IntroductionReminderOptOutMember.hash_member_id(
                            interaction_member.id
                        )
                    )
                except IntroductionReminderOptOutMember.DoesNotExist:
                    pass
                else:
                    await introduction_reminder_opt_out_member.adelete()

                button.style = discord.ButtonStyle.red
                button.label = "Opt-out of introduction reminders"
                button.emoji = discord.PartialEmoji.from_str(
                    emoji.emojize(":no_good:", language="alias")
                )

                await interaction.response.edit_message(view=self)

    @tasks.loop(**settings["GET_ROLES_REMINDER_INTERVAL"])
    async def get_roles_reminder(self) -> None:
        """
        Recurring task to send an opt-in roles reminder message to Discord members' DMs.

        The opt-in reminder message suggests that the Discord member has not given themselves
        any of the optional opt-in roles.

        See README.md for the full list of conditions for when these
        reminders are sent.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        guest_role: discord.Role | None = await self.bot.guest_role
        if not guest_role:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        roles_channel_mention: str = "`#roles`"
        roles_channel: discord.TextChannel | None = await self.bot.roles_channel
        if roles_channel:
            roles_channel_mention = roles_channel.mention

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

            async for log in guild.audit_logs(action=AuditLogAction.member_role_update):
                if log.target == member:
                    if guest_role not in log.before.roles and guest_role in log.after.roles:
                        guest_role_received_time = log.created_at
                        break
            else:
                logging.error(
                    f"Member with ID: {member.id} could not be checked"
                    " whether to send role_reminder,"
                    " because their \"guest_role_received_time\" could not be found."
                )
                continue

            hashed_member_id: str = SentGetRolesReminderMember.hash_member_id(member.id)

            time_since_role_received: datetime.timedelta = (
                    discord.utils.utcnow() - guest_role_received_time
            )
            if time_since_role_received > datetime.timedelta(days=1):
                sent_get_roles_reminder_member_exists: bool = (
                    await SentGetRolesReminderMember.objects.filter(
                        hashed_member_id=hashed_member_id
                    ).aexists()
                )
                if not sent_get_roles_reminder_member_exists:
                    await member.send(
                        "Hey! It seems like you joined the CSS Discord server and been given"
                        " the `@Guest` role but have not yet nabbed yourself any opt-in roles."
                        f"\nYou can head to {roles_channel_mention} and click on the icons"
                        " to get optional roles like pronouns and year group identifiers",
                    )

                await SentGetRolesReminderMember.objects.acreate(
                    hashed_member_id=hashed_member_id
                )

    @clear_reminder_backlog.before_loop
    @kick_no_introduction_members.before_loop
    @introduction_reminder.before_loop
    @get_roles_reminder.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()


def setup(bot: TeXBot) -> None:
    """
    Add the tasks cog to the bot.

    This is called at startup, to load all the cogs onto the bot.
    """
    bot.add_cog(TasksCog(bot))
