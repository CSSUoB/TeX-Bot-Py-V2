"""
Contains settings values and setup functions.

Settings values are imported from the tex-bot-deployment.yaml file.
These values are used to configure the functionality of the bot at run-time.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ("SettingsAccessor",)


import contextlib
import logging
import os
import re
from logging import Logger
from pathlib import Path
from typing import Any, ClassVar, Final

from strictyaml import YAML

from exceptions import BotRequiresRestartAfterConfigChange
from ._yaml import load_yaml
from .constants import REQUIRES_RESTART_SETTINGS_KEYS, PROJECT_ROOT

logger: Final[Logger] = logging.getLogger("TeX-Bot")


def _get_settings_file_path() -> Path:
    settings_file_not_found_message: str = (
        "No settings file was found. "
        "Please make sure you have created a `TeX-Bot-deployment.yaml` file."
    )

    raw_settings_file_path: str | None = (
        os.getenv("TEX_BOT_SETTINGS_FILE_PATH", None)
        or os.getenv("TEX_BOT_SETTINGS_FILE", None)
        or os.getenv("TEX_BOT_SETTINGS_PATH", None)
        or os.getenv("TEX_BOT_SETTINGS", None)
        or os.getenv("TEX_BOT_CONFIG_FILE_PATH", None)
        or os.getenv("TEX_BOT_CONFIG_FILE", None)
        or os.getenv("TEX_BOT_CONFIG_PATH", None)
        or os.getenv("TEX_BOT_CONFIG", None)
        or os.getenv("TEX_BOT_DEPLOYMENT_FILE_PATH", None)
        or os.getenv("TEX_BOT_DEPLOYMENT_FILE", None)
        or os.getenv("TEX_BOT_DEPLOYMENT_PATH", None)
        or os.getenv("TEX_BOT_DEPLOYMENT", None)
    )

    if raw_settings_file_path:
        settings_file_not_found_message = (
            "A path to the settings file location was provided by environment variable, "
            "however this path does not refer to an existing file."
        )
    else:
        logger.debug(
            (
                "Settings file location not supplied by environment variable, "
                "falling back to `Tex-Bot-deployment.yaml`."
            ),
        )
        raw_settings_file_path = "TeX-Bot-deployment.yaml"
        if not (PROJECT_ROOT / Path(raw_settings_file_path)).exists():
            raw_settings_file_path = "TeX-Bot-settings.yaml"

            if not (PROJECT_ROOT / Path(raw_settings_file_path)).exists():
                raw_settings_file_path = "TeX-Bot-config.yaml"

    settings_file_path: Path = Path(raw_settings_file_path)

    if not settings_file_path.is_file():
        raise FileNotFoundError(settings_file_not_found_message)

    return settings_file_path


class SettingsAccessor:
    """
    Settings class that provides access to all settings values.

    Settings values can be accessed via key (like a dictionary) or via class attribute.
    """

    _settings: ClassVar[dict[str, object]] = {}
    _most_recent_yaml: ClassVar[YAML | None] = None  # type: ignore[no-any-unimported]

    @classmethod
    def format_invalid_settings_key_message(cls, item: str) -> str:
        """Return the message to state that the given settings key is invalid."""
        return f"{item!r} is not a valid settings key."

    def __getattr__(self, item: str) -> Any:  # type: ignore[misc]  # noqa: ANN401
        """Retrieve settings value by attribute lookup."""
        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

        if "_pytest" in item or item in ("__bases__", "__test__"):  # NOTE: Overriding __getattr__() leads to many edge-case issues where external libraries will attempt to call getattr() with peculiar values
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if self._most_recent_yaml is None:
            with contextlib.suppress(BotRequiresRestartAfterConfigChange):
                self.reload()

        if item in self._settings:
            return self._settings[item]

        if re.match(r"\A[A-Z](?:[A-Z_]*[A-Z])?\Z", item):
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = (
                self.format_invalid_settings_key_message(item)
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

    def __getitem__(self, item: str) -> Any:  # type: ignore[misc]  # noqa: ANN401
        """Retrieve settings value by key lookup."""
        attribute_not_exist_error: AttributeError
        try:
            return getattr(self, item)
        except AttributeError as attribute_not_exist_error:
            key_error_message: str = item

            ERROR_WAS_FROM_INVALID_KEY_NAME: Final[bool] = (
                self.format_invalid_settings_key_message(item) in str(
                    attribute_not_exist_error,
                )
            )
            if ERROR_WAS_FROM_INVALID_KEY_NAME:
                key_error_message = str(attribute_not_exist_error)

            raise KeyError(key_error_message) from None

    @classmethod
    def reload(cls) -> None:
        current_yaml: YAML = load_yaml(_get_settings_file_path().read_text())  # type: ignore[no-any-unimported]

        if current_yaml == cls._most_recent_yaml:
            return

        changed_settings_keys: set[str] = set()

        if cls._reload_console_logging(current_yaml["console-log-level"]):
            changed_settings_keys.add("console-log-level")

        if cls._reload_discord_log_channel_log_level(current_yaml["discord-log-channel-log-level"]):
            changed_settings_keys.add("discord-log-channel-log-level")

        cls._most_recent_yaml = current_yaml

        if changed_settings_keys & REQUIRES_RESTART_SETTINGS_KEYS:
            raise BotRequiresRestartAfterConfigChange(changed_settings=changed_settings_keys)

    @classmethod
    def _reload_console_logging(cls, console_log_level: str) -> bool:
        CONSOLE_LOG_LEVEL_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or console_log_level != cls._most_recent_yaml["console-log-level"]
        )
        if not CONSOLE_LOG_LEVEL_CHANGED:
            return False

        logger.setLevel(getattr(logging, console_log_level))

        logger.handlers.clear()

        console_logging_handler: logging.Handler = logging.StreamHandler()
        # noinspection SpellCheckingInspection
        console_logging_handler.setFormatter(
            logging.Formatter(
                "{asctime} | {name} | {levelname:^8} - {message}",
                style="{",
            ),
        )
        logger.addHandler(console_logging_handler)

        logger.propagate = False

        return True

    @classmethod
    def _reload_discord_log_channel_log_level(cls, discord_log_channel_log_level: str) -> bool:
        raise NotImplementedError
