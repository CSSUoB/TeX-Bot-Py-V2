"""File to hold cog classes related to moderation actions and tracking."""

import logging
from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = ("ModerationCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class ModerationCog(TeXBotBaseCog):
    """Cog to track moderation actions and report them to the committee."""

    most_recently_deleted_message: discord.Message | None = None

    @TeXBotBaseCog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Listen for message deletions."""
        if message.guild is None or message.author.bot or message.guild != self.bot.main_guild:
            return

        self.most_recently_deleted_message = message

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_audit_log_entry(self, entry: discord.AuditLogEntry) -> None:
        """Listen for audit log entries."""
        committee_role: discord.Role = await self.bot.committee_role

        if (
            entry.action != discord.AuditLogAction.message_delete
            or not self.most_recently_deleted_message
        ):
            return

        deleter: discord.Member | discord.User | None = entry.user
        author: discord.User | discord.Member | None = entry.target
        channel: discord.TextChannel | None = entry.extra.channel  # type: ignore[union-attr]

        if (
            not isinstance(channel, discord.TextChannel)
            or not isinstance(author, discord.Member)
            or not isinstance(deleter, discord.Member)
        ):
            return

        if (
            author != self.most_recently_deleted_message.author
            or channel != self.most_recently_deleted_message.channel
            or committee_role in author.roles
        ):
            return

        await self.send_message_to_committee(self.most_recently_deleted_message, deleter)

        self.most_recently_deleted_message = None
