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
    from collections.abc import Set as AbstractSet
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

    This exists to catch the case where a committee member deletes somebody else's message
    but forgets to run the "Report Message to Committee" command beforehand: a copy of the
    deleted message is sent to the message-reports channel, so that it is still retained.

    Only individual deletions are tracked. Bulk deletions (channel purges) are deliberately
    not covered, as those are not the single forgotten-report case this exists to catch.

    Discord sends the content of a deleted message (in the message-delete gateway event)
    separately from who deleted it (in the audit-log-entry gateway event),
    so deleted messages are retained until their matching audit-log entry arrives.
    Messages that users delete themselves never gain an audit-log entry,
    so those are simply discarded once they expire.
    """

    # NOTE: Deletions are held only for the moment between the two gateway events that describe them, so this bound just prevents unbounded growth if audit-log entries stop arriving. Expiry is what normally empties the store
    MAXIMUM_PENDING_DELETED_MESSAGES: "Final[int]" = 25
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

    def _take_pending_deleted_messages(
        self, *, author_id: int, channel_id: int, count: int
    ) -> "Sequence[discord.Message]":
        """
        Remove & return the retained deleted messages matching the given audit-log entry.

        At most `count` messages are returned, taking the most recently deleted matches:
        the audit-log entry states how many deletions it covers, so any older match is left
        pending rather than being wrongly attributed to this entry. A message that its own
        author deleted never gains an audit-log entry, so is only ever discarded on expiry.

        Any retained messages that have been waiting for an audit-log entry for longer than
        `PENDING_DELETED_MESSAGE_EXPIRY` are discarded.
        """
        EXPIRY_CUTOFF: Final[datetime.datetime] = (
            discord.utils.utcnow() - self.PENDING_DELETED_MESSAGE_EXPIRY
        )

        unexpired_messages: Sequence[_PendingDeletedMessage] = [
            pending_deleted_message
            for pending_deleted_message in self._pending_deleted_messages
            if pending_deleted_message.deleted_at >= EXPIRY_CUTOFF
        ]

        if count < 1:
            self._pending_deleted_messages = deque(
                unexpired_messages, maxlen=self.MAXIMUM_PENDING_DELETED_MESSAGES
            )
            return ()

        MATCHED_INDEXES: Final[Sequence[int]] = [
            index
            for index, pending_deleted_message in enumerate(unexpired_messages)
            if pending_deleted_message.message.channel.id == channel_id
            and pending_deleted_message.message.author.id == author_id
        ]
        TAKEN_INDEXES: Final[AbstractSet[int]] = frozenset(MATCHED_INDEXES[-count:])

        self._pending_deleted_messages = deque(
            (
                pending_deleted_message
                for index, pending_deleted_message in enumerate(unexpired_messages)
                if index not in TAKEN_INDEXES
            ),
            maxlen=self.MAXIMUM_PENDING_DELETED_MESSAGES,
        )

        return [unexpired_messages[index].message for index in sorted(TAKEN_INDEXES)]

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
        if message.author.bot or message.guild != self.bot.main_guild:
            return

        self._pending_deleted_messages.append(
            _PendingDeletedMessage(deleted_at=discord.utils.utcnow(), message=message)
        )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_audit_log_entry(self, entry: discord.AuditLogEntry) -> None:
        """Report any retained messages that the given audit-log entry says were deleted."""
        # NOTE: The action is filtered before any shortcut accessors are used, so that entries of every other action type (role updates, kicks, bans, etc.) do not repeatedly hit the guild & role accessors
        if entry.action is not discord.AuditLogAction.message_delete:
            return

        if not isinstance(entry.target, (discord.Member, discord.User)):
            return

        deleter: discord.User | discord.Member | None = entry.user
        if deleter is None or deleter == self.bot.user:
            return

        # NOTE: Discord does not guarantee that the message-delete gateway event arrives before the audit-log entry describing it, so a short grace period is given for it to catch up. This also allows a single audit-log entry to collect a whole burst of rapid deletions, which Discord aggregates into that one entry
        await asyncio.sleep(self.AUDIT_LOG_ENTRY_GRACE_PERIOD)

        deleted_messages: Sequence[discord.Message] = self._take_pending_deleted_messages(
            author_id=entry.target.id,
            # NOTE: `extra.channel` is a bare `discord.Object` whenever the deleted message was sent within a thread, so only the channel's ID can be relied upon here
            channel_id=entry.extra.channel.id,  # type: ignore[union-attr]
            count=entry.extra.count,  # type: ignore[union-attr]
        )

        if deleted_messages:
            await self._report_deleted_messages(deleted_messages, deleter)
