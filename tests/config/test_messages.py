"""Test suite for loading the response messages TeX-Bot sends into Discord."""

import json
from typing import TYPE_CHECKING

import pytest

from config._messages import (
    MESSAGES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME,
    MessagesAccessor,
)
from exceptions import (
    ImproperlyConfiguredError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path
    from typing import Final

    type MessagesWriter = "Callable[[object], Path]"

__all__: "Sequence[str]" = ()


VALID_MESSAGES: "Final[Mapping[str, object]]" = {
    "welcome_messages": ["Welcome!", "Hello there!"],
    "roles_messages": ["Get your roles here."],
}


@pytest.fixture()
def write_messages(tmp_path: "Path", monkeypatch: pytest.MonkeyPatch) -> "MessagesWriter":
    """Return a callable writing the given messages & pointing TeX-Bot at them."""

    def _write_messages(raw_messages: object) -> "Path":
        messages_file_path: Path = tmp_path / "messages.json"
        messages_file_path.write_text(
            raw_messages if isinstance(raw_messages, str) else json.dumps(raw_messages),
            encoding="utf-8",
        )
        monkeypatch.setenv(
            MESSAGES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, str(messages_file_path)
        )
        return messages_file_path

    return _write_messages


class TestLoading:
    """Test case for reading the messages file."""

    @staticmethod
    def test_valid_messages_are_loaded(write_messages: "MessagesWriter") -> None:
        """Test that both sets of messages are read from a valid file."""
        write_messages(VALID_MESSAGES)
        messages: MessagesAccessor = MessagesAccessor()

        messages.reload()

        assert messages.is_loaded
        assert messages.welcome_messages == frozenset({"Welcome!", "Hello there!"})
        assert messages.roles_messages == frozenset({"Get your roles here."})

    @staticmethod
    def test_accessing_messages_before_loading_is_refused() -> None:
        """Test that reading messages before any are loaded is refused."""
        messages: MessagesAccessor = MessagesAccessor()

        assert not messages.is_loaded

        with pytest.raises(RuntimeError, match="before they have been loaded"):
            _ = messages.welcome_messages

    @staticmethod
    def test_a_missing_file_is_reported(
        tmp_path: "Path", monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that naming a messages file that does not exist is reported clearly."""
        monkeypatch.setenv(
            MESSAGES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, str(tmp_path / "absent.json")
        )

        with pytest.raises(ImproperlyConfiguredError, match="must be a path"):
            MessagesAccessor().reload()

    @staticmethod
    def test_malformed_json_is_reported(write_messages: "MessagesWriter") -> None:
        """Test that a file that is not valid JSON is reported clearly."""
        write_messages("{not valid json")

        with pytest.raises(ImproperlyConfiguredError, match="decoded"):
            MessagesAccessor().reload()

    @staticmethod
    @pytest.mark.parametrize("raw_messages", (["a", "list"], "a string", 42))
    def test_json_that_is_not_an_object_is_reported(
        write_messages: "MessagesWriter", raw_messages: object
    ) -> None:
        """Test that a messages file not holding an object of message sets is rejected."""
        write_messages(raw_messages)

        with pytest.raises(ImproperlyConfiguredError, match="decoded"):
            MessagesAccessor().reload()


class TestMessageSetValidation:
    """Test case for the structure each set of messages must have."""

    @staticmethod
    @pytest.mark.parametrize("missing_key", ("welcome_messages", "roles_messages"))
    def test_a_missing_message_set_is_reported(
        write_messages: "MessagesWriter", missing_key: str
    ) -> None:
        """Test that omitting either set of messages is reported clearly."""
        write_messages(
            {key: value for key, value in VALID_MESSAGES.items() if key != missing_key}
        )

        with pytest.raises(MessagesJSONFileMissingKeyError):
            MessagesAccessor().reload()

    @staticmethod
    @pytest.mark.parametrize("invalid_value", ([], None, 42, {}))
    def test_an_empty_or_non_iterable_message_set_is_reported(
        write_messages: "MessagesWriter", invalid_value: object
    ) -> None:
        """Test that a set of messages that holds no messages is rejected."""
        write_messages({**VALID_MESSAGES, "welcome_messages": invalid_value})

        with pytest.raises(MessagesJSONFileValueError):
            MessagesAccessor().reload()

    @staticmethod
    def test_a_string_is_not_accepted_as_a_set_of_messages(
        write_messages: "MessagesWriter",
    ) -> None:
        """
        Test that a single string is not treated as a set of messages.

        A string is iterable, so without an explicit check it would be accepted and
        silently split into one message per character.
        """
        write_messages({**VALID_MESSAGES, "welcome_messages": "Welcome!"})

        with pytest.raises(MessagesJSONFileValueError):
            MessagesAccessor().reload()

    @staticmethod
    def test_an_object_is_not_accepted_as_a_set_of_messages(
        write_messages: "MessagesWriter",
    ) -> None:
        """
        Test that a JSON object is not treated as a set of messages.

        An object is iterable too, so without an explicit check it would be accepted and
        silently reduced to its own keys, discarding every message it holds.
        """
        write_messages({**VALID_MESSAGES, "welcome_messages": {"Welcome!": "Hello there!"}})

        with pytest.raises(MessagesJSONFileValueError):
            MessagesAccessor().reload()

    @staticmethod
    def test_messages_that_are_not_strings_are_read_as_text(
        write_messages: "MessagesWriter",
    ) -> None:
        """Test that a message written as a number is read as the text of that number."""
        write_messages({**VALID_MESSAGES, "roles_messages": [42, "Get your roles here."]})
        messages: MessagesAccessor = MessagesAccessor()

        messages.reload()

        assert messages.roles_messages == frozenset({"42", "Get your roles here."})


class TestFailedReloads:
    """Test case for what happens when messages cannot be reloaded."""

    @staticmethod
    def test_a_failed_reload_leaves_previously_loaded_messages_intact(
        write_messages: "MessagesWriter",
    ) -> None:
        """
        Test that failing to reload does not discard the messages already loaded.

        Both sets are read before either is stored, so a file that is only partly
        valid cannot leave one set updated and the other stale.
        """
        write_messages(VALID_MESSAGES)
        messages: MessagesAccessor = MessagesAccessor()
        messages.reload()

        write_messages({"welcome_messages": ["Still valid."]})

        with pytest.raises(MessagesJSONFileMissingKeyError):
            messages.reload()

        assert messages.welcome_messages == frozenset({"Welcome!", "Hello there!"})
        assert messages.roles_messages == frozenset({"Get your roles here."})


def test_messages_are_deduplicated(write_messages: "MessagesWriter") -> None:
    """Test that a message repeated within the file is only held once."""
    write_messages({**VALID_MESSAGES, "roles_messages": ["Same", "Same", "Different"]})
    messages: MessagesAccessor = MessagesAccessor()

    messages.reload()

    assert messages.roles_messages == frozenset({"Same", "Different"})
