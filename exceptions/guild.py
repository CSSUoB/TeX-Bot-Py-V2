"""Custom exception classes to be raised when errors occur with access properties of a Discord guild object."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "DiscordMemberNotInMainGuildError",
    "EveryoneRoleCouldNotBeRetrievedError",
)

from classproperties import classproperty

from .base import BaseErrorWithErrorCode, BaseTeXBotError


class DiscordMemberNotInMainGuildError(BaseTeXBotError, ValueError):
    """Exception class for when no members of your Discord guild have the given user ID."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "Given user ID does not represent any member of your group's Discord guild."

    def __init__(self, message: str | None = None, user_id: int | None = None) -> None:
        """Initialize a ValueError exception for a non-existent user ID."""
        self.user_id: int | None = user_id

        super().__init__(message)


class EveryoneRoleCouldNotBeRetrievedError(BaseErrorWithErrorCode, ValueError):
    """Exception class for when the "@everyone" role could not be retrieved."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "The reference to the \"@everyone\" role could not be correctly retrieved."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1042"
