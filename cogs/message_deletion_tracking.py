"""Contains cog classes for tracking messages deleted by moderators."""

import asyncio
import datetime
import logging
from collections import deque
from typing import TYPE_CHECKING, NamedTuple, override

import discord

from exceptions import MessageReportsChannelDoesNotExistError
from utils import MessageReportAction, TeXBotBaseCog, send_message_report_to_committee
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBot


__all__: "Sequence[str]" = ("MessageDeletionTrackingCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class _PendingDeletedMessage(NamedTuple):
    """A deleted message, awaiting the audit-log entry that names who deleted it."""

    deleted_at: datetime.datetime
    message: discord.Message


class MessageDeletionTrackingCog(TeXBotBaseCog):
    """
    Cog class defining the event listeners for reporting moderator-deleted messages.

    When a message is deleted by somebody other than its author, a copy of that message is
    sent to the message-reports channel, so that it is retained for committee to review.

    Discord sends the content of a deleted message (in the message-delete gateway event)
    separately from who deleted it (in the audit-log-entry gateway event),
    so deleted messages are retained until their matching audit-log entry arrives.
    Messages that users delete themselves never gain an audit-log entry,
    so those are simply discarded once they expire.
    """

    MAXIMUM_PENDING_DELETED_MESSAGES: "Final[int]" = 100
    PENDING_DELETED_MESSAGE_EXPIRY: "Final[datetime.timedelta]" = datetime.timedelta(
        seconds=30
    )
    AUDIT_LOG_ENTRY_GRACE_PERIOD: "Final[float]" = 2.0

    @override
    def __init__(self, bot: "TeXBot") -> None:
        """Initialise the store of deleted messages awaiting their audit-log entry."""
        self._pending_deleted_messages: deque[_PendingDeletedMessage] = deque(
            maxlen=self.MAXIMUM_PENDING_DELETED_MESSAGES
        )

        super().__init__(bot)

    def _store_pending_deleted_messages(self, *messages: discord.Message) -> None:
        """Retain the given deleted messages until their audit-log entry arrives."""
        MAIN_GUILD: Final[discord.Guild] = self.bot.main_guild
        DELETED_AT: Final[datetime.datetime] = discord.utils.utcnow()

        message: discord.Message
        for message in messages:
            if message.author.bot or message.guild != MAIN_GUILD:
                continue

            self._pending_deleted_messages.append(
                _PendingDeletedMessage(deleted_at=DELETED_AT, message=message)
            )

    def _take_pending_deleted_messages(
        self, *, author_id: int | None, channel_id: int
    ) -> "Sequence[discord.Message]":
        """
        Remove & return the retained deleted messages matching the given audit-log entry.

        An `author_id` of `None` matches every author within the given channel, because
        bulk deletions are recorded against only the channel that was purged.

        Any retained messages that have been waiting for an audit-log entry for longer than
        `PENDING_DELETED_MESSAGE_EXPIRY` are discarded.
        """
        EXPIRY_CUTOFF: Final[datetime.datetime] = (
            discord.utils.utcnow() - self.PENDING_DELETED_MESSAGE_EXPIRY
        )

        matched_messages: list[discord.Message] = []
        retained_messages: deque[_PendingDeletedMessage] = deque(
            maxlen=self.MAXIMUM_PENDING_DELETED_MESSAGES
        )

        pending_deleted_message: _PendingDeletedMessage
        for pending_deleted_message in self._pending_deleted_messages:
            if pending_deleted_message.deleted_at < EXPIRY_CUTOFF:
                continue

            deleted_message: discord.Message = pending_deleted_message.message

            MATCHES_AUDIT_LOG_ENTRY: bool = deleted_message.channel.id == channel_id and (
                author_id is None or deleted_message.author.id == author_id
            )

            if MATCHES_AUDIT_LOG_ENTRY:
                matched_messages.append(deleted_message)
            else:
                retained_messages.append(pending_deleted_message)

        self._pending_deleted_messages = retained_messages

        return matched_messages

    async def _report_deleted_messages(
        self,
        deleted_messages: "Sequence[discord.Message]",
        deleter: discord.User | discord.Member,
    ) -> None:
        """Send a copy of each of the given deleted messages to the message-reports channel."""
        committee_role: discord.Role = await self.bot.committee_role

        message_reports_channel_error: MessageReportsChannelDoesNotExistError
        try:
            deleted_message: discord.Message
            for deleted_message in deleted_messages:
                SELF_DELETED: bool = deleted_message.author == deleter
                # NOTE: Committee members deleting one another's messages is treated as housekeeping rather than as a moderation action, so is never reported
                AUTHORED_BY_COMMITTEE: bool = (
                    isinstance(deleted_message.author, discord.Member)
                    and committee_role in deleted_message.author.roles
                )

                if SELF_DELETED or AUTHORED_BY_COMMITTEE:
                    continue

                await send_message_report_to_committee(
                    self.bot,
                    message=deleted_message,
                    reporting_user=deleter,
                    action=MessageReportAction.DELETED,
                )
        except MessageReportsChannelDoesNotExistError as message_reports_channel_error:
            logger.error(  # noqa: TRY400
                "Could not report deleted messages to committee: %s",
                message_reports_channel_error.message,
            )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_message_delete(self, message: discord.Message) -> None:
        """Retain a deleted message until its audit-log entry names who deleted it."""
        self._store_pending_deleted_messages(message)

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_bulk_message_delete(self, messages: "Sequence[discord.Message]") -> None:
        """Retain bulk-deleted messages until their audit-log entry names who deleted them."""
        self._store_pending_deleted_messages(*messages)

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_audit_log_entry(self, entry: discord.AuditLogEntry) -> None:
        """Report any retained messages that the given audit-log entry says were deleted."""
        # NOTE: The action is filtered before any shortcut accessors are used, so that entries of every other action type (role updates, kicks, bans, etc.) do not repeatedly hit the guild & role accessors
        audit_log_entry_author_id: int | None
        audit_log_entry_channel_id: int

        if entry.action is discord.AuditLogAction.message_delete:
            if not isinstance(entry.target, (discord.Member, discord.User)):
                return

            audit_log_entry_author_id = entry.target.id
            # NOTE: `extra.channel` is a bare `discord.Object` whenever the deleted message was sent within a thread, so only the channel's ID can be relied upon here
            audit_log_entry_channel_id = entry.extra.channel.id  # type: ignore[union-attr]

        elif entry.action is discord.AuditLogAction.message_bulk_delete:
            TARGET_IS_CHANNEL: Final[bool] = isinstance(
                entry.target, (discord.abc.GuildChannel, discord.Thread, discord.Object)
            )
            if not TARGET_IS_CHANNEL:
                return

            # NOTE: Bulk deletions are recorded against only the channel that was purged, so every retained message within that channel is reported
            audit_log_entry_author_id = None
            audit_log_entry_channel_id = entry.target.id

        else:
            return

        deleter: discord.User | discord.Member | None = entry.user
        if deleter is None or deleter == self.bot.user:
            return

        # NOTE: Discord does not guarantee that the message-delete gateway events arrive before the audit-log entry describing them, so a short grace period is given for them to catch up. This also allows a single audit-log entry to collect a whole burst of rapid deletions, which Discord aggregates into that one entry
        await asyncio.sleep(self.AUDIT_LOG_ENTRY_GRACE_PERIOD)

        deleted_messages: Sequence[discord.Message] = self._take_pending_deleted_messages(
            author_id=audit_log_entry_author_id, channel_id=audit_log_entry_channel_id
        )

        if deleted_messages:
            await self._report_deleted_messages(deleted_messages, deleter)
