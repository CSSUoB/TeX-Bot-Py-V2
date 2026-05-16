"""Custom exception classes raised when errors occur during use of the "/strike" command."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "NoAuditLogsStrikeTrackingError",
    "StrikeTrackingError",
)


from typing import override

from classproperties import classproperty

from .base import BaseTeXBotError


class StrikeTrackingError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when any error occurs while tracking moderation actions.

    If this error occurs, it is likely that manually applied moderation actions will be missed
    and not tracked correctly.
    """

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "An error occurred while trying to track manually applied moderation actions."


class NoAuditLogsStrikeTrackingError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when there are no audit logs to resolve the committee member.

    If this error occurs, it is likely that manually applied moderation actions will be missed
    and not tracked correctly.
    """

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "Unable to retrieve audit log entry after possible manual moderation action."
