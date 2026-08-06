"""
Loading of the response messages that TeX-Bot sends into Discord.

Messages are held separately from the deployment configuration: they are a body of
content rather than a set of settings, so they live in their own JSON file and are
neither validated by the settings schema nor editable through the `/config` command.
"""

import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from exceptions import (
    ImproperlyConfiguredError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final


__all__: "Sequence[str]" = ("MESSAGES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME", "MessagesAccessor")


PROJECT_ROOT: "Final[Path]" = Path(__file__).parent.parent.resolve()

DEFAULT_MESSAGES_FILE_NAME: "Final[str]" = "messages.json"

MESSAGES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME: "Final[str]" = "MESSAGES_FILE_PATH"


def _get_messages_file_path() -> Path:
    """Locate the messages JSON file."""
    RAW_MESSAGES_FILE_PATH: Final[str | None] = os.getenv(
        MESSAGES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME
    )

    messages_file_path: Path = (
        Path(RAW_MESSAGES_FILE_PATH.strip())
        if RAW_MESSAGES_FILE_PATH
        else PROJECT_ROOT / DEFAULT_MESSAGES_FILE_NAME
    )

    if not messages_file_path.is_file():
        MESSAGES_FILE_DOES_NOT_EXIST_MESSAGE: str = (
            f"{MESSAGES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME} must be a path "
            f"to a file that exists."
        )
        raise ImproperlyConfiguredError(MESSAGES_FILE_DOES_NOT_EXIST_MESSAGE)

    return messages_file_path


def _load_messages_file() -> "Mapping[str, object]":
    """Read & decode the messages JSON file."""
    JSON_DECODING_ERROR_MESSAGE: Final[str] = (
        "Messages JSON file must contain a JSON string that can be decoded "
        "into a Python dict object."
    )

    json_decode_error: json.JSONDecodeError
    try:
        raw_messages: object = json.loads(
            _get_messages_file_path().read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as json_decode_error:
        raise ImproperlyConfiguredError(JSON_DECODING_ERROR_MESSAGE) from json_decode_error

    if not isinstance(raw_messages, dict):
        raise ImproperlyConfiguredError(JSON_DECODING_ERROR_MESSAGE)

    return raw_messages


def _get_message_set(raw_messages: "Mapping[str, object]", key: str) -> frozenset[str]:
    """Retrieve a single set of messages from the decoded messages file."""
    if key not in raw_messages:
        raise MessagesJSONFileMissingKeyError(missing_key=key)

    value: object = raw_messages[key]

    KEY_IS_VALID: Final[bool] = bool(
        isinstance(value, Iterable) and not isinstance(value, (str, bytes)) and value
    )
    if not KEY_IS_VALID:
        raise MessagesJSONFileValueError(dict_key=key, invalid_value=value)

    if TYPE_CHECKING:
        assert isinstance(value, Iterable)

    return frozenset(str(single_message) for single_message in value)


class MessagesAccessor:
    """Provides access to the response messages that TeX-Bot sends into Discord."""

    def __init__(self) -> None:
        """Initialise an accessor holding no messages until they are first loaded."""
        self._welcome_messages: frozenset[str] | None = None
        self._roles_messages: frozenset[str] | None = None

    @property
    def is_loaded(self) -> bool:
        """Whether any messages have been loaded yet."""
        return self._welcome_messages is not None and self._roles_messages is not None

    def reload(self) -> None:
        """
        Load the messages JSON file, replacing any previously loaded messages.

        Both sets of messages are read before either is stored, so a malformed file
        leaves any previously loaded messages untouched.
        """
        RAW_MESSAGES: Final[Mapping[str, object]] = _load_messages_file()

        WELCOME_MESSAGES: Final[frozenset[str]] = _get_message_set(
            RAW_MESSAGES, "welcome_messages"
        )
        ROLES_MESSAGES: Final[frozenset[str]] = _get_message_set(
            RAW_MESSAGES, "roles_messages"
        )

        self._welcome_messages = WELCOME_MESSAGES
        self._roles_messages = ROLES_MESSAGES

    def _get_loaded(self, messages: frozenset[str] | None) -> frozenset[str]:
        """Return the given set of messages, raising if they have not been loaded."""
        if messages is None:
            MESSAGES_NOT_LOADED_MESSAGE: str = (
                "Messages cannot be accessed before they have been loaded."
            )
            raise RuntimeError(MESSAGES_NOT_LOADED_MESSAGE)

        return messages

    @property
    def welcome_messages(self) -> frozenset[str]:
        """The set of messages welcoming a new member into the community group."""
        return self._get_loaded(self._welcome_messages)

    @property
    def roles_messages(self) -> frozenset[str]:
        """The set of messages describing the opt-in roles that a member can request."""
        return self._get_loaded(self._roles_messages)
