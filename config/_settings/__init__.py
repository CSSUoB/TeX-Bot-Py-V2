"""
Contains settings values and setup functions.

Settings values are imported from the tex-bot-deployment.yaml file.
These values are used to configure the functionality of the bot at run-time.
"""

import datetime
import logging
import re
from typing import TYPE_CHECKING

import utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import ClassVar, Final

    from strictyaml import YAML


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class SettingsAccessor:
    """
    Settings class that provides access to the settings values.

    Settings values can be accessed via key (like a dictionary) or via class attributes.
    """

    _settings: "ClassVar[dict[str, object]]" = {}
    _most_recent_yaml: "ClassVar[YAML | None]" = None

    @classmethod
    def _get_invalid_settings_key_message(cls, item: str) -> str:
        """Return the message to state that the given settings key is invalid."""
        return f"{item!r} is not a valid settings key."

    @classmethod
    async def restore_default(cls, config_setting_name: str) -> None:
        """
        Set the specified setting to its default value.

        If the setting does not have a default, it will be removed.
        """
        return

    def __getattr__(self, item: str) -> object:
        """Retrieve settings value by attribute lookup."""
        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

        if "_pytest" in item or item in ("__bases__", "__test__"):  # NOTE: Overriding __getattr__() leads to many edge-case issues where external libraries will attempt to call getattr() with peculiar values
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        IN_SETTING_KEY_FORMAT: Final[bool] = bool(
            re.fullmatch(r"\A(?!.*__.*)(?:[A-Z]|[A-Z_][A-Z]|[A-Z_][A-Z][A-Z_]*[A-Z])\Z", item)
        )
        if not IN_SETTING_KEY_FORMAT:
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if self._most_recent_yaml is None:
            YAML_NOT_LOADED_MESSAGE: Final[str] = (
                "Configuration cannot be accessed before it is loaded."
            )
            raise RuntimeError(YAML_NOT_LOADED_MESSAGE)

        if item not in self._settings:
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = self._get_invalid_settings_key_message(
                item,
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        ATTEMPTING_TO_ACCESS_BOT_TOKEN_WHEN_ALREADY_RUNNING: Final[bool] = bool(
            "bot" in item.lower() and "token" in item.lower() and utils.is_running_in_async()
        )
        if ATTEMPTING_TO_ACCESS_BOT_TOKEN_WHEN_ALREADY_RUNNING:
            TEX_BOT_ALREADY_RUNNING_MESSAGE: Final[str] = (
                f"Cannot access {item!r} when TeX-Bot is already running."
            )
            raise RuntimeError(TEX_BOT_ALREADY_RUNNING_MESSAGE)

        return self._settings[item]

    def __getitem__(self, item: str) -> object:
        """Retrieve settings value by key lookup."""
        attribute_not_exist_error: AttributeError
        try:
            return getattr(self, item)
        except AttributeError as attribute_not_exist_error:
            key_error_message: str = item

            ERROR_WAS_FROM_INVALID_KEY_NAME: Final[bool] = (
                self._get_invalid_settings_key_message(item) in str(
                    attribute_not_exist_error,
                )
            )
            if ERROR_WAS_FROM_INVALID_KEY_NAME:
                key_error_message = str(attribute_not_exist_error)

            raise KeyError(key_error_message) from None

