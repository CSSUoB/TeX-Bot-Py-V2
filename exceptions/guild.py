"""Custom exception classes raised when errors occur with properties of a guild object."""

from typing import TYPE_CHECKING, override

from typed_classproperties import classproperty

from .base import BaseErrorWithErrorCode, BaseTeXBotError

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: Sequence[str] = (
    "DiscordMemberNotInMainGuildError",
    "EveryoneRoleCouldNotBeRetrievedError",
)


class DiscordMemberNotInMainGuildError(BaseTeXBotError, ValueError):
    """Exception class for when no members of your Discord guild have the given user ID."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "Given user ID does not represent any member of your group's Discord guild."

    @override
    def __init__(self, message: str | None = None, user_id: int | None = None) -> None:
        """Initialise a ValueError exception for a non-existent user ID."""
        self.user_id: int | None = user_id

        super().__init__(message)


class EveryoneRoleCouldNotBeRetrievedError(BaseErrorWithErrorCode, ValueError):
    """Exception class for when the "@everyone" role could not be retrieved."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return 'The reference to the "@everyone" role could not be correctly retrieved.'

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1042"
