import datetime
import functools
import logging
from typing import Final

import discord
from discord.ext import tasks

from cogs._utils import TeXBotCog
from db.core.models import DiscordReminder
from utils import TeXBot


class ClearRemindersBacklogTaskCog(TeXBotCog):
    def __init__(self, bot: TeXBot) -> None:
        """Start all task managers when this cog is initialised."""
        self.clear_reminders_backlog.start()

        super().__init__(bot)

    def cog_unload(self) -> None:
        """
        Unload hook that ends all running tasks whenever the tasks cog is unloaded.

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
                discord.ChannelType.private_thread}
        )

        reminder: DiscordReminder
        async for reminder in DiscordReminder.objects.all():
            time_since_reminder_needed_to_be_sent: datetime.timedelta = (
                    discord.utils.utcnow() - reminder.send_datetime
            )
            if time_since_reminder_needed_to_be_sent > datetime.timedelta(minutes=15):
                user: discord.User | None = discord.utils.find(
                    functools.partial(
                        lambda _user, _reminder: (
                            not _user.bot
                            and DiscordReminder.hash_member_id(_user.id) == _reminder.hashed_member_id  # noqa: E501
                        ),
                        _reminder=reminder
                    ),
                    self.bot.users
                )

                if not user:
                    logging.warning(
                        "User with hashed user ID: %s no longer exists.",
                        reminder.hashed_member_id
                    )
                    await reminder.adelete()
                    continue

                channel: discord.PartialMessageable = self.bot.get_partial_messageable(
                    reminder.channel_id,
                    type=(
                        discord.ChannelType(reminder.channel_type.value)
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

    @clear_reminders_backlog.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()
