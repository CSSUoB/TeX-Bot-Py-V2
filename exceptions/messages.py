"""Custom exception classes raised when errors occur with retrieving messages from the file."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "InvalidMessagesJSONFileError",
    "MessagesJSONFileMissingKeyError",
    "MessagesJSONFileValueError",
)


from typing import override

from classproperties import classproperty

from .config_changes import ImproperlyConfiguredError


class InvalidMessagesJSONFileError(ImproperlyConfiguredError):
    """Exception class to raise when the messages.json file has an invalid structure."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "The messages JSON file has an invalid structure at the given key."

    @override
    def __init__(self, message: str | None = None, dict_key: str | None = None) -> None:
        """Initialize an ImproperlyConfigured exception for an invalid messages.json file."""
        self.dict_key: str | None = dict_key

        super().__init__(message)


class MessagesJSONFileMissingKeyError(InvalidMessagesJSONFileError):
    """Exception class to raise when a key in the messages.json file is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "The messages JSON file is missing a required key."

    @override
    def __init__(self, message: str | None = None, missing_key: str | None = None) -> None:
        """Initialize a new InvalidMessagesJSONFile exception for a missing key."""
        super().__init__(message, dict_key=missing_key)

    @property
    def missing_key(self) -> str | None:
        """The key that was missing from the messages.json file."""
        return self.dict_key

    @missing_key.setter
    def missing_key(self, value: str | None) -> None:
        self.dict_key = value


class MessagesJSONFileValueError(InvalidMessagesJSONFileError):
    """Exception class to raise when a key in the messages.json file has an invalid value."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "The messages JSON file has an invalid value."

    @override
    def __init__(self, message: str | None = None, dict_key: str | None = None, invalid_value: object | None = None) -> None:  # noqa: E501
        """Initialize a new InvalidMessagesJSONFile exception for a key's invalid value."""
        self.invalid_value: object | None = invalid_value

        super().__init__(message, dict_key)
