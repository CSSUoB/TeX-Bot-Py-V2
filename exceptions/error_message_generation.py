"""Custom exception classes related to generating error messages to send to the user."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = ("ErrorCodeCouldNotBeIdentifiedError",)


from typing import override

from typed_classproperties import classproperty

from .base import BaseTeXBotError


class ErrorCodeCouldNotBeIdentifiedError(BaseTeXBotError, Exception):
    """Exception class to raise when the error code could not be identified from an error."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "The error code could not be retrieved from the given error."

    @override
    def __init__(
        self,
        message: str | None = None,
        other_error: Exception | type[Exception] | None = None,
    ) -> None:
        """Initialize an exception for a non-existent error code."""
        self.other_error: Exception | type[Exception] | None = other_error

        super().__init__(message)
