"""Custom exception classes for committee-action tracking."""

from collections.abc import Sequence

__all__: Sequence[str] = ()


from typing import override

from classproperties import classproperty

from .base import BaseTeXBotError


class InvalidActionTargetError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when the desired target of a committee action is invalid.

    This could be that the target user is not in the server.
    """

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "The target of the action is invalid."


class InvalidActionDescriptionError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when the description of a committee action is invalid.

    This could be due to it being too long, or some other validation issue.
    """

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "The description of the action is invalid."
