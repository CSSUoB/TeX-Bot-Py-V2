"""Custom exception classes raised when errors occur with properties of a guild object."""

__all__: Sequence[str] = (
    "DiscordMemberNotInMainGuildError",
    "EveryoneRoleCouldNotBeRetrievedError",
    "RoleNotFoundInMainGuildError",
)

from typing import override
lazy from collections.abc import Sequence

from typed_classproperties import classproperty

from .base import BaseErrorWithErrorCode, BaseTeXBotError


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


class RoleNotFoundInMainGuildError(BaseTeXBotError, ValueError):
    """Exception class for when no roles of your Discord guild have the given role ID."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "Given role ID does not represent any role of your group's Discord guild."

    @override
    def __init__(self, message: str | None = None, role_id: int | None = None) -> None:
        """Initialise a ValueError exception for a non-existent role ID."""
        self.role_id: int | None = role_id

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
