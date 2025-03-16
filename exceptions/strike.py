"""Custom exception classes raised when errors occur during use of the "/strike" command."""

from typing import TYPE_CHECKING, override

from typed_classproperties import classproperty

from .base import BaseTeXBotError

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "NoAuditLogsStrikeTrackingError",
    "StrikeTrackingError",
)


class StrikeTrackingError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when any error occurs while tracking moderation actions.

    If this error occurs, it is likely that manually applied moderation actions will be missed
    and not tracked correctly.
    """

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "An error occurred while trying to track manually applied moderation actions."


class NoAuditLogsStrikeTrackingError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when there are no audit logs to resolve the committee member.

    If this error occurs, it is likely that manually applied moderation actions will be missed
    and not tracked correctly.
    """

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "Unable to retrieve audit log entry after possible manual moderation action."
