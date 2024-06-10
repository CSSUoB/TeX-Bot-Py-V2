from collections.abc import Sequence

__all__: Sequence[str] = ("MessagesAccessor",)


import json
import re
from typing import Any, ClassVar, Final

from aiopath import AsyncPath

from config.constants import MESSAGES_LOCALE_CODES, PROJECT_ROOT


class MessagesAccessor:
    _messages: ClassVar[dict[str, str | set[str] | Sequence[str]]] = {}
    _messages_already_loaded: ClassVar[bool] = False

    @classmethod
    def format_invalid_message_id_message(cls, item: str) -> str:
        """Return the message to state that the given message ID is invalid."""
        return f"{item!r} is not a valid message ID."

    def __getattr__(self, item: str) -> Any:  # type: ignore[misc]  # noqa: ANN401
        """Retrieve message(s) value by attribute lookup."""
        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

        if "_pytest" in item or item in ("__bases__", "__test__"):  # NOTE: Overriding __getattr__() leads to many edge-case issues where external libraries will attempt to call getattr() with peculiar values
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        IN_MESSAGE_KEY_FORMAT: Final[bool] = bool(
            re.fullmatch(r"\A(?!.*__.*)(?:[A-Z]|[A-Z_][A-Z]|[A-Z_][A-Z][A-Z_]*[A-Z])\Z", item)  # noqa: COM812
        )
        if not IN_MESSAGE_KEY_FORMAT:
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if item not in self._messages:
            INVALID_MESSAGE_ID_MESSAGE: Final[str] = (
                self.format_invalid_message_id_message(item)
            )
            raise AttributeError(INVALID_MESSAGE_ID_MESSAGE)

        return self._messages[item]

    def __getitem__(self, item: str) -> Any:  # type: ignore[misc]  # noqa: ANN401
        """Retrieve message(s) value by key lookup."""
        attribute_not_exist_error: AttributeError
        try:
            return getattr(self, item)
        except AttributeError as attribute_not_exist_error:
            key_error_message: str = item

            ERROR_WAS_FROM_INVALID_KEY_NAME: Final[bool] = (
                self.format_invalid_message_id_message(item) in str(
                    attribute_not_exist_error,
                )
            )
            if ERROR_WAS_FROM_INVALID_KEY_NAME:
                key_error_message = str(attribute_not_exist_error)

            raise KeyError(key_error_message) from None

    @classmethod
    async def load(cls, messages_locale_code: str) -> None:
        if messages_locale_code not in MESSAGES_LOCALE_CODES:
            INVALID_MESSAGES_LOCALE_CODE_MESSAGE: Final[str] = (
                f"{"messages_locale_code"!r} must be one of "
                f"'{"', '".join(MESSAGES_LOCALE_CODES)}'"
            )
            raise ValueError(INVALID_MESSAGES_LOCALE_CODE_MESSAGE)

        if cls._messages_already_loaded:
            MESSAGES_ALREADY_LOADED_MESSAGE: Final[str] = "Messages have already been loaded."
            raise RuntimeError(MESSAGES_ALREADY_LOADED_MESSAGE)

        NO_MESSAGES_FILE_FOUND_ERROR: Final[RuntimeError] = RuntimeError(
            f"No messages file found for locale: {messages_locale_code!r}",
        )

        try:
            # noinspection PyTypeChecker
            messages_locale_file_path: AsyncPath = await anext(
                path
                async for path
                in (AsyncPath(PROJECT_ROOT) / "config/_messages/locales/").iterdir()
                if path.stem == messages_locale_code
            )
        except StopIteration:
            raise NO_MESSAGES_FILE_FOUND_ERROR from None

        if not await messages_locale_file_path.is_file():
            raise NO_MESSAGES_FILE_FOUND_ERROR

        messages_load_error: Exception
        try:
            raw_messages: object = json.loads(await messages_locale_file_path.read_text())

            if not hasattr(raw_messages, "__getitem__"):
                raise TypeError

            # noinspection PyUnresolvedReferences
            cls._messages["WELCOME_MESSAGES"] = set(raw_messages["welcome-messages"])
            # noinspection PyUnresolvedReferences
            cls._messages["OPT_IN_ROLES_SELECTORS"] = tuple(
                raw_messages["opt-in-roles-selectors"],
            )

        except (json.JSONDecodeError, TypeError, KeyError) as messages_load_error:
            INVALID_MESSAGES_FILE_MESSAGE: Final[str] = (
                "Messages file contained invalid contents."
            )
            raise ValueError(INVALID_MESSAGES_FILE_MESSAGE) from messages_load_error

        cls._messages_already_loaded = True
