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

from discord_logging.handler import DiscordHandler
from strictyaml import YAML

from ._pre_startup_utils import is_running_in_async
from exceptions import BotRequiresRestartAfterConfigChange

from ._yaml import load_yaml
from .constants import (
    DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME,
    PROJECT_ROOT,
    REQUIRES_RESTART_SETTINGS,
)

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

        if not re.match(r"\A(?!.*__.*)(?:[A-Z]|[A-Z_][A-Z]|[A-Z_][A-Z][A-Z_]*[A-Z])\Z", item):
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if self._most_recent_yaml is None:
            with contextlib.suppress(BotRequiresRestartAfterConfigChange):
                self.reload()

        if item not in self._settings:
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = (
                self.format_invalid_settings_key_message(item)
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        ATTEMPTING_TO_ACCESS_BOT_TOKEN_WHEN_ALREADY_RUNNING: Final[bool] = bool(
            "bot" in item.lower()
            and "token" in item.lower()
            and is_running_in_async()
        )
        if ATTEMPTING_TO_ACCESS_BOT_TOKEN_WHEN_ALREADY_RUNNING:
            raise RuntimeError(f"Cannot access {item!r} when TeX-Bot is already running.")

        return self._settings[item]

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

        changed_settings_keys.update(
            cls._reload_console_logging(current_yaml["logging"]["console"]),
            cls._reload_discord_log_channel_logging(
                current_yaml["logging"].get("discord-channel", None),
            ),
            cls._reload_discord_bot_token(current_yaml["discord"]["bot-token"]),
            cls._reload_discord_main_guild_id(current_yaml["discord"]["main-guild-id"]),
            cls._reload_community_group_full_name(
                current_yaml["community-group"].get("full-name", None),
            ),
        )

        cls._most_recent_yaml = current_yaml

        if changed_settings_keys & REQUIRES_RESTART_SETTINGS:
            raise BotRequiresRestartAfterConfigChange(changed_settings=changed_settings_keys)

    @classmethod
    def _reload_console_logging(cls, console_logging_settings: YAML) -> set[str]:
        """
        Reload the console logging configuration with the new given log level.

        Returns the set of settings keys that have been changed.
        """
        CONSOLE_LOGGING_SETTINGS_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or console_logging_settings != cls._most_recent_yaml["logging"]["console"]
        )
        if not CONSOLE_LOGGING_SETTINGS_CHANGED:
            return set()

        stream_handlers: set[logging.StreamHandler] = {
            handler
            for handler
            in logger.handlers
            if isinstance(handler, logging.StreamHandler)
        }
        if len(stream_handlers) > 1:
            raise ValueError("Cannot determine which logging stream-handler to update.")

        console_logging_handler: logging.StreamHandler = logging.StreamHandler()

        if len(stream_handlers) == 0:
            # noinspection SpellCheckingInspection
            console_logging_handler.setFormatter(
                logging.Formatter(
                    "{asctime} | {name} | {levelname:^8} - {message}",
                    style="{",
                ),
            )
            logger.setLevel(1)
            logger.addHandler(console_logging_handler)
            logger.propagate = False

        elif len(stream_handlers) == 1:
            console_logging_handler = stream_handlers.pop()

        else:
            raise ValueError

        console_logging_handler.setLevel(
            getattr(logging, console_logging_settings["log-level"].data)
        )

        return {"logging:console:log-level"}

    @classmethod
    def _reload_discord_log_channel_logging(cls, discord_channel_logging_settings: YAML | None) -> set[str]:  # noqa: E501
        """
        Reload the Discord log channel logging configuration.

        Returns the set of settings keys that have been changed.
        """
        DISCORD_CHANNEL_LOGGING_SETTINGS_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or discord_channel_logging_settings != cls._most_recent_yaml["logging"].get(
                "discord-channel",
                None,
            )
            or "DISCORD_LOG_CHANNEL_WEBHOOK_URL" not in cls._settings
        )
        if not DISCORD_CHANNEL_LOGGING_SETTINGS_CHANGED:
            return set()

        cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = (
            discord_channel_logging_settings
            if discord_channel_logging_settings is None
            else discord_channel_logging_settings["webhook_url"].data
        )

        discord_logging_handlers: set[DiscordHandler] = {
            handler for handler in logger.handlers if isinstance(handler, DiscordHandler)
        }
        if len(discord_logging_handlers) > 1:
            raise ValueError(
                "Cannot determine which logging Discord-webhook-handler to update."
            )

        discord_logging_handler_display_name: str = (
            DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME
        )
        discord_logging_handler_avatar_url: str | None = None

        if len(discord_logging_handlers) == 1:
            existing_discord_logging_handler: DiscordHandler = discord_logging_handlers.pop()

            ONLY_DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED: Final[bool] = bool(
                discord_channel_logging_settings is not None
                and cls._most_recent_yaml["logging"].get("discord-channel", None) is not None
                and all(
                    value == cls._most_recent_yaml["logging"]["discord-channel"].get(key, None)
                    for key, value
                    in discord_channel_logging_settings.items()
                    if key != "log-level"
                )
            )
            if ONLY_DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED:
                DISCORD_LOG_CHANNEL_LOG_LEVEL_IS_SAME: Final[bool] = bool(
                    discord_channel_logging_settings["log-level"] == cls._most_recent_yaml[
                        "logging"
                    ]["discord-channel"]["log-level"]
                )
                if DISCORD_LOG_CHANNEL_LOG_LEVEL_IS_SAME:
                    raise ValueError(
                        "Assumed Discord log channel log level had changed, but it hadn't."
                    )

                existing_discord_logging_handler.setLevel(
                    getattr(logging, discord_channel_logging_settings["log-level"].data)
                )
                return {"logging:discord-channel:log-level"}

            discord_logging_handler_display_name = existing_discord_logging_handler.name
            discord_logging_handler_avatar_url = existing_discord_logging_handler.avatar_url
            logger.removeHandler(existing_discord_logging_handler)

            if discord_channel_logging_settings is None:
                return {"logging:discord-channel:webhook-url"}

        elif len(discord_logging_handlers) == 0 and discord_channel_logging_settings is None:
            return set()

        discord_logging_handler: logging.Handler = DiscordHandler(
            discord_logging_handler_display_name,
            discord_channel_logging_settings["webhook-url"],
            avatar_url=discord_logging_handler_avatar_url,
        )
        discord_logging_handler.setLevel(
            getattr(logging, discord_channel_logging_settings["log-level"].data)
        )
        # noinspection SpellCheckingInspection
        discord_logging_handler.setFormatter(
            logging.Formatter("{levelname} | {message}", style="{"),
        )

        logger.addHandler(discord_logging_handler)

        changed_settings: set[str] = {"logging:discord-channel:webhook-url"}

        DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml["logging"].get("discord-channel", None) is None
            or discord_channel_logging_settings["log-level"] != cls._most_recent_yaml[
                "logging"
            ]["discord-channel"]["log-level"]
        )
        if DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED:
            changed_settings.add("logging:discord-channel:log-level")

        return changed_settings

    @classmethod
    def _reload_discord_bot_token(cls, discord_bot_token: YAML) -> set[str]:
        """
        Reload the Discord bot-token.

        Returns the set of settings keys that have been changed.
        """
        DISCORD_BOT_TOKEN_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or discord_bot_token != cls._most_recent_yaml["discord"]["bot-token"]
            or "DISCORD_BOT_TOKEN" not in cls._settings
        )
        if not DISCORD_BOT_TOKEN_CHANGED:
            return set()

        cls._settings["DISCORD_BOT_TOKEN"] = discord_bot_token.data

        return {"discord:bot-token"}

    @classmethod
    def _reload_discord_main_guild_id(cls, discord_main_guild_id: YAML) -> set[str]:
        """
        Reload the Discord main-guild ID.

        Returns the set of settings keys that have been changed.
        """
        DISCORD_MAIN_GUILD_ID_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or discord_main_guild_id != cls._most_recent_yaml["discord"]["main-guild-id"]
            or "_DISCORD_MAIN_GUILD_ID" not in cls._settings
        )
        if not DISCORD_MAIN_GUILD_ID_CHANGED:
            return set()

        cls._settings["_DISCORD_MAIN_GUILD_ID"] = discord_main_guild_id.data

        return {"discord:main-guild-id"}

    @classmethod
    def _reload_community_group_full_name(cls, community_group_full_name: YAML | None) -> set[str]:
        """
        Reload the community-group full name.

        Returns the set of settings keys that have been changed.
        """
        COMMUNITY_GROUP_FULL_NAME_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or community_group_full_name != cls._most_recent_yaml["community-group"].get(
                "full-name",
                None,
            )
            or "_COMMUNITY_GROUP_FULL_NAME" not in cls._settings
        )
        if not COMMUNITY_GROUP_FULL_NAME_CHANGED:
            return set()

        cls._settings["_COMMUNITY_GROUP_FULL_NAME"] = (
            community_group_full_name
            if community_group_full_name is None
            else community_group_full_name.data
        )

        return {"community-group:full-name"}

    # TODO: Load more config settings
