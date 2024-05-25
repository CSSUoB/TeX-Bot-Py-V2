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
        "Please make sure you have created a `tex-bot-deployment.yaml` file."
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
        raw_settings_file_path = "tex-bot-deployment.yaml"
        if not (PROJECT_ROOT / Path(raw_settings_file_path)).exists():
            raw_settings_file_path = "tex-bot-settings.yaml"

            if not (PROJECT_ROOT / Path(raw_settings_file_path)).exists():
                raw_settings_file_path = "tex-bot-config.yaml"

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
        settings_file_path: Path = _get_settings_file_path()
        current_yaml: YAML = load_yaml(  # type: ignore[no-any-unimported]
            settings_file_path.read_text(),
            file_name=settings_file_path.name,
        )

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
            cls._reload_group_full_name(
                current_yaml["community-group"].get("full-name", None),
            ),
            cls._reload_group_short_name(
                current_yaml["community-group"].get("short-name", None),
            ),
            cls._reload_purchase_membership_link(
                current_yaml["community-group"]["links"].get("purchase-membership"),
            ),
            cls._reload_membership_perks_link(
                current_yaml["community-group"]["links"].get("membership-perks"),
            ),
            cls._reload_moderation_document_link(
                current_yaml["community-group"]["links"]["moderation-document"],
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
    def _reload_group_full_name(cls, group_full_name: YAML | None) -> set[str]:
        """
        Reload the community-group full name.

        Returns the set of settings keys that have been changed.
        """
        GROUP_FULL_NAME_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or group_full_name != cls._most_recent_yaml["community-group"].get(
                "full-name",
                None,
            )
            or "_GROUP_FULL_NAME" not in cls._settings
        )
        if not GROUP_FULL_NAME_CHANGED:
            return set()

        cls._settings["_GROUP_FULL_NAME"] = (
            group_full_name
            if group_full_name is None
            else group_full_name.data
        )

        return {"community-group:full-name"}

    @classmethod
    def _reload_group_short_name(cls, group_short_name: YAML | None) -> set[str]:
        """
        Reload the community-group short name.

        Returns the set of settings keys that have been changed.
        """
        GROUP_SHORT_NAME_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or group_short_name != cls._most_recent_yaml["community-group"].get(
                "short-name",
                None,
            )
            or "_GROUP_SHORT_NAME" not in cls._settings
        )
        if not GROUP_SHORT_NAME_CHANGED:
            return set()

        cls._settings["_GROUP_SHORT_NAME"] = (
            group_short_name
            if group_short_name is None
            else group_short_name.data
        )

        return {"community-group:short-name"}

    @classmethod
    def _reload_purchase_membership_link(cls, purchase_membership_link: YAML | None) -> set[str]:
        """
        Reload the link to allow people to purchase a membership.

        Returns the set of settings keys that have been changed.
        """
        PURCHASE_MEMBERSHIP_LINK_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or purchase_membership_link != cls._most_recent_yaml["community-group"][
                "links"
            ].get("purchase-membership", None)
            or "PURCHASE_MEMBERSHIP_LINK" not in cls._settings
        )
        if not PURCHASE_MEMBERSHIP_LINK_CHANGED:
            return set()

        cls._settings["PURCHASE_MEMBERSHIP_LINK"] = (
            purchase_membership_link
            if purchase_membership_link is None
            else purchase_membership_link.data
        )

        return {"community-group:links:purchase-membership"}

    @classmethod
    def _reload_membership_perks_link(cls, membership_perks_link: YAML | None) -> set[str]:
        """
        Reload the link to view the perks of getting a membership to join your community group.

        Returns the set of settings keys that have been changed.
        """
        MEMBERSHIP_PERKS_LINK_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or membership_perks_link != cls._most_recent_yaml["community-group"][
                "links"
            ].get("membership-perks", None)
            or "MEMBERSHIP_PERKS_LINK" not in cls._settings
        )
        if not MEMBERSHIP_PERKS_LINK_CHANGED:
            return set()

        cls._settings["MEMBERSHIP_PERKS_LINK"] = (
            membership_perks_link
            if membership_perks_link is None
            else membership_perks_link.data
        )

        return {"community-group:links:membership-perks"}

    @classmethod
    def _reload_moderation_document_link(cls, moderation_document_link: YAML) -> set[str]:
        """
        Reload the link to view your community group's moderation document.

        Returns the set of settings keys that have been changed.
        """
        MODERATION_DOCUMENT_LINK_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or moderation_document_link != cls._most_recent_yaml["community-group"]["links"][
                "moderation-document"
            ]
            or "MODERATION_DOCUMENT_LINK" not in cls._settings
        )
        if not MODERATION_DOCUMENT_LINK_CHANGED:
            return set()

        cls._settings["MODERATION_DOCUMENT_LINK"] = moderation_document_link.data

        return {"community-group:links:moderation-document"}

    # TODO: Load more config settings
