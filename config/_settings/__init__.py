"""
Contains settings values and setup functions.

Settings values are imported from the tex-bot-deployment.yaml file.
These values are used to configure the functionality of the bot at run-time.
"""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "get_settings_file_path",
    "SettingsAccessor",
    "view_single_config_setting_value",
    "assign_single_config_setting_value",
)


import contextlib
import logging
import os
import re
from collections.abc import Iterable, Mapping
from datetime import timedelta
from logging import Logger
from pathlib import Path
from typing import Any, ClassVar, Final, TextIO, TypeAlias

import strictyaml
from discord_logging.handler import DiscordHandler
from strictyaml import YAML

from config.constants import (
    DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME,
    PROJECT_ROOT,
)
from exceptions import (
    BotRequiresRestartAfterConfigChange,
    ChangingSettingWithRequiredSiblingError,
)

from . import utils
from ._yaml import load_yaml

NestedMapping: TypeAlias = Mapping[str, "NestedMapping | str"]

logger: Final[Logger] = logging.getLogger("TeX-Bot")


def get_settings_file_path() -> Path:
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
        if not (PROJECT_ROOT / raw_settings_file_path).exists():
            raw_settings_file_path = "tex-bot-settings.yaml"

            if not (PROJECT_ROOT / raw_settings_file_path).exists():
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
    _most_recent_yaml: ClassVar[YAML | None] = None

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
            and utils.is_running_in_async(),
        )
        if ATTEMPTING_TO_ACCESS_BOT_TOKEN_WHEN_ALREADY_RUNNING:
            TEX_BOT_ALREADY_RUNNING_MESSAGE: Final[str] = (
                f"Cannot access {item!r} when TeX-Bot is already running."
            )
            raise RuntimeError(TEX_BOT_ALREADY_RUNNING_MESSAGE)

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
        settings_file_path: Path = get_settings_file_path()
        current_yaml: YAML = load_yaml(  # TODO: better error messages when loading yaml
            settings_file_path.read_text(),
            file_name=settings_file_path.name,
        )

        if current_yaml == cls._most_recent_yaml and cls._settings:
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
                current_yaml["community-group"]["links"].get("purchase-membership", None),
            ),
            cls._reload_membership_perks_link(
                current_yaml["community-group"]["links"].get("membership-perks", None),
            ),
            cls._reload_moderation_document_link(
                current_yaml["community-group"]["links"]["moderation-document"],
            ),
            cls._reload_members_list_url(
                current_yaml["community-group"]["members-list"]["url"],
            ),
            cls._reload_members_list_auth_session_cookie(
                current_yaml["community-group"]["members-list"]["auth-session-cookie"],
            ),
            cls._reload_members_list_id_format(
                current_yaml["community-group"]["members-list"]["id-format"],
            ),
            cls._reload_ping_command_easter_egg_probability(
                current_yaml["commands"]["ping"]["easter-egg-probability"],
            ),
            cls._reload_stats_command_lookback_days(
                current_yaml["commands"]["stats"]["lookback-days"],
            ),
            cls._reload_stats_command_displayed_roles(
                current_yaml["commands"]["stats"]["displayed-roles"],
            ),
            cls._reload_stats_command_displayed_roles(
                current_yaml["commands"]["strike"]["timeout-duration"],
            ),
            cls._reload_strike_performed_manually_warning_location(
                current_yaml["commands"]["strike"]["performed-manually-warning-location"],
            ),
            cls._reload_messages_locale_code(current_yaml["messages-locale-code"]),
            cls._reload_send_introduction_reminders_enabled(
                current_yaml["reminders"]["send-introduction-reminders"]["enabled"],
            ),
            cls._reload_send_introduction_reminders_delay(
                current_yaml["reminders"]["send-introduction-reminders"]["delay"],
            ),
            cls._reload_send_introduction_reminders_interval(
                current_yaml["reminders"]["send-introduction-reminders"]["interval"],
            ),
            cls._reload_send_get_roles_reminders_enabled(
                current_yaml["reminders"]["send-get-roles-reminders"]["enabled"],
            ),
            cls._reload_send_get_roles_reminders_delay(
                current_yaml["reminders"]["send-get-roles-reminders"]["delay"],
            ),
            cls._reload_send_get_roles_reminders_interval(
                current_yaml["reminders"]["send-get-roles-reminders"]["interval"],
            ),
        )

        cls._most_recent_yaml = current_yaml

    @classmethod
    def _reload_console_logging(cls, console_logging_settings: YAML) -> set[str]:  # type: ignore[misc]
        """
        Reload the console logging configuration with the new given log level.

        Returns the set of settings keys that have been changed.
        """
        CONSOLE_LOGGING_SETTINGS_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or console_logging_settings != cls._most_recent_yaml["logging"]["console"],
        )
        if not CONSOLE_LOGGING_SETTINGS_CHANGED:
            return set()

        stream_handlers: set[logging.StreamHandler[TextIO]] = {
            handler
            for handler
            in logger.handlers
            if isinstance(handler, logging.StreamHandler)
        }
        if len(stream_handlers) > 1:
            CANNOT_DETERMINE_LOGGING_HANDLER_MESSAGE: Final[str] = (
                "Cannot determine which logging stream-handler to update."
            )
            raise ValueError(CANNOT_DETERMINE_LOGGING_HANDLER_MESSAGE)

        console_logging_handler: logging.StreamHandler[TextIO] = logging.StreamHandler()

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
            getattr(logging, console_logging_settings["log-level"].data),
        )

        return {"logging:console:log-level"}

    @classmethod
    def _reload_discord_log_channel_logging(cls, discord_channel_logging_settings: YAML | None) -> set[str]:  # type: ignore[misc] # noqa: E501
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
            or "DISCORD_LOG_CHANNEL_WEBHOOK_URL" not in cls._settings,
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
            CANNOT_DETERMINE_LOGGING_HANDLER_MESSAGE: Final[str] = (
                "Cannot determine which logging Discord-webhook-handler to update."
            )
            raise ValueError(CANNOT_DETERMINE_LOGGING_HANDLER_MESSAGE)

        discord_logging_handler_display_name: str = (
            DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME
        )
        discord_logging_handler_avatar_url: str | None = None

        if len(discord_logging_handlers) == 1:
            existing_discord_logging_handler: DiscordHandler = discord_logging_handlers.pop()

            ONLY_DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED: Final[bool] = bool(
                discord_channel_logging_settings is not None
                and cls._most_recent_yaml is not None
                and cls._most_recent_yaml["logging"].get("discord-channel", None) is not None
                and all(
                    value == cls._most_recent_yaml["logging"]["discord-channel"].get(key, None)
                    for key, value
                    in discord_channel_logging_settings.items()
                    if key != "log-level"
                ),
            )
            if ONLY_DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED:
                DISCORD_LOG_CHANNEL_LOG_LEVEL_IS_SAME: Final[bool] = bool(
                    discord_channel_logging_settings["log-level"] == cls._most_recent_yaml[  # type: ignore[index]
                        "logging"
                    ]["discord-channel"]["log-level"],
                )
                if DISCORD_LOG_CHANNEL_LOG_LEVEL_IS_SAME:
                    LOG_LEVEL_DIDNT_CHANGE_MESSAGE: Final[str] = (
                        "Assumed Discord log channel log level had changed, but it hadn't."
                    )
                    raise ValueError(LOG_LEVEL_DIDNT_CHANGE_MESSAGE)

                existing_discord_logging_handler.setLevel(
                    getattr(logging, discord_channel_logging_settings["log-level"].data),  # type: ignore[index]
                )
                return {"logging:discord-channel:log-level"}

            discord_logging_handler_display_name = existing_discord_logging_handler.name
            discord_logging_handler_avatar_url = existing_discord_logging_handler.avatar_url
            logger.removeHandler(existing_discord_logging_handler)

            if discord_channel_logging_settings is None:
                return {"logging:discord-channel:webhook-url"}

        elif len(discord_logging_handlers) == 0 and discord_channel_logging_settings is None:
            return set()

        if discord_channel_logging_settings is None:
            raise RuntimeError

        discord_logging_handler: logging.Handler = DiscordHandler(
            discord_logging_handler_display_name,
            discord_channel_logging_settings["webhook-url"],
            avatar_url=discord_logging_handler_avatar_url,
        )
        discord_logging_handler.setLevel(
            getattr(logging, discord_channel_logging_settings["log-level"].data),
        )
        # noinspection SpellCheckingInspection
        discord_logging_handler.setFormatter(
            logging.Formatter("{levelname} | {message}", style="{"),
        )

        logger.addHandler(discord_logging_handler)

        changed_settings: set[str] = {"logging:discord-channel:webhook-url"}

        DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or cls._most_recent_yaml["logging"].get("discord-channel", None) is None
            or discord_channel_logging_settings["log-level"] != cls._most_recent_yaml[
                "logging"
            ]["discord-channel"]["log-level"],
        )
        if DISCORD_LOG_CHANNEL_LOG_LEVEL_CHANGED:
            changed_settings.add("logging:discord-channel:log-level")

        return changed_settings

    @classmethod
    def _reload_discord_bot_token(cls, discord_bot_token: YAML) -> set[str]:  # type: ignore[misc]
        """
        Reload the Discord bot-token.

        Returns the set of settings keys that have been changed.
        """
        DISCORD_BOT_TOKEN_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or discord_bot_token != cls._most_recent_yaml["discord"]["bot-token"]
            or "DISCORD_BOT_TOKEN" not in cls._settings,
        )
        if not DISCORD_BOT_TOKEN_CHANGED:
            return set()

        cls._settings["DISCORD_BOT_TOKEN"] = discord_bot_token.data

        return {"discord:bot-token"}

    @classmethod
    def _reload_discord_main_guild_id(cls, discord_main_guild_id: YAML) -> set[str]:  # type: ignore[misc]
        """
        Reload the Discord main-guild ID.

        Returns the set of settings keys that have been changed.
        """
        DISCORD_MAIN_GUILD_ID_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or discord_main_guild_id != cls._most_recent_yaml["discord"]["main-guild-id"]
            or "_DISCORD_MAIN_GUILD_ID" not in cls._settings,
        )
        if not DISCORD_MAIN_GUILD_ID_CHANGED:
            return set()

        cls._settings["_DISCORD_MAIN_GUILD_ID"] = discord_main_guild_id.data

        return {"discord:main-guild-id"}

    @classmethod
    def _reload_group_full_name(cls, group_full_name: YAML | None) -> set[str]:  # type: ignore[misc]
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
            or "_GROUP_FULL_NAME" not in cls._settings,
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
    def _reload_group_short_name(cls, group_short_name: YAML | None) -> set[str]:  # type: ignore[misc]
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
            or "_GROUP_SHORT_NAME" not in cls._settings,
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
    def _reload_purchase_membership_link(cls, purchase_membership_link: YAML | None) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the link to allow people to purchase a membership.

        Returns the set of settings keys that have been changed.
        """
        PURCHASE_MEMBERSHIP_LINK_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or purchase_membership_link != cls._most_recent_yaml["community-group"][
                "links"
            ].get("purchase-membership", None)
            or "PURCHASE_MEMBERSHIP_LINK" not in cls._settings,
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
    def _reload_membership_perks_link(cls, membership_perks_link: YAML | None) -> set[str]:  # type: ignore[misc]
        """
        Reload the link to view the perks of getting a membership to join your community group.

        Returns the set of settings keys that have been changed.
        """
        MEMBERSHIP_PERKS_LINK_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or membership_perks_link != cls._most_recent_yaml["community-group"][
                "links"
            ].get("membership-perks", None)
            or "MEMBERSHIP_PERKS_LINK" not in cls._settings,
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
    def _reload_moderation_document_link(cls, moderation_document_link: YAML) -> set[str]:  # type: ignore[misc]
        """
        Reload the link to view your community group's moderation document.

        Returns the set of settings keys that have been changed.
        """
        MODERATION_DOCUMENT_LINK_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or moderation_document_link != cls._most_recent_yaml["community-group"]["links"][
                "moderation-document"
            ]
            or "MODERATION_DOCUMENT_LINK" not in cls._settings,
        )
        if not MODERATION_DOCUMENT_LINK_CHANGED:
            return set()

        cls._settings["MODERATION_DOCUMENT_LINK"] = moderation_document_link.data

        return {"community-group:links:moderation-document"}

    @classmethod
    def _reload_members_list_url(cls, members_list_url: YAML) -> set[str]:  # type: ignore[misc]
        """
        Reload the url that points to the location of your community group's members-list.

        Returns the set of settings keys that have been changed.
        """
        MEMBERS_LIST_URL_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or members_list_url != cls._most_recent_yaml["community-group"]["members-list"][
                "url"
            ]
            or "MEMBERS_LIST_URL" not in cls._settings,
        )
        if not MEMBERS_LIST_URL_CHANGED:
            return set()

        cls._settings["MEMBERS_LIST_URL"] = members_list_url.data

        return {"community-group:members-list:url"}

    @classmethod
    def _reload_members_list_auth_session_cookie(cls, members_list_auth_session_cookie: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the auth session cookie used to authenticate to access your members-list.

        Returns the set of settings keys that have been changed.
        """
        MEMBERS_LIST_AUTH_SESSION_COOKIE_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or members_list_auth_session_cookie != cls._most_recent_yaml["community-group"][
                "members-list"
            ]["auth-session-cookie"]
            or "MEMBERS_LIST_AUTH_SESSION_COOKIE" not in cls._settings,
        )
        if not MEMBERS_LIST_AUTH_SESSION_COOKIE_CHANGED:
            return set()

        cls._settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"] = (
            members_list_auth_session_cookie.data
        )

        return {"community-group:members-list:auth-session-cookie"}

    @classmethod
    def _reload_members_list_id_format(cls, members_list_id_format: YAML) -> set[str]:  # type: ignore[misc]
        """
        Reload the format regex matcher for IDs in your community group's members-list.

        Returns the set of settings keys that have been changed.
        """
        MEMBERS_LIST_ID_FORMAT_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or members_list_id_format != cls._most_recent_yaml["community-group"][
                "members-list"
            ]["id-format"]
            or "MEMBERS_LIST_ID_FORMAT" not in cls._settings,
        )
        if not MEMBERS_LIST_ID_FORMAT_CHANGED:
            return set()

        cls._settings["MEMBERS_LIST_ID_FORMAT"] = members_list_id_format.data

        return {"community-group:members-list:id-format"}

    @classmethod
    def _reload_ping_command_easter_egg_probability(cls, ping_command_easter_egg_probability: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the probability that the rarer response will show when using the ping command.

        Returns the set of settings keys that have been changed.
        """
        PING_COMMAND_EASTER_EGG_PROBABILITY_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or ping_command_easter_egg_probability != cls._most_recent_yaml["commands"][
                "ping"
            ]["easter-egg-probability"]
            or "PING_COMMAND_EASTER_EGG_PROBABILITY" not in cls._settings,
        )
        if not PING_COMMAND_EASTER_EGG_PROBABILITY_CHANGED:
            return set()

        cls._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
            ping_command_easter_egg_probability.data
        )

        return {"commands:ping:easter-egg-probability"}

    @classmethod
    def _reload_stats_command_lookback_days(cls, stats_command_lookback_days: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the number of days to lookback for statistics.

        Returns the set of settings keys that have been changed.
        """
        STATS_COMMAND_LOOKBACK_DAYS_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or stats_command_lookback_days != cls._most_recent_yaml["commands"][
                "stats"
            ]["lookback-days"]
            or "STATS_COMMAND_LOOKBACK_DAYS" not in cls._settings,
        )
        if not STATS_COMMAND_LOOKBACK_DAYS_CHANGED:
            return set()

        cls._settings["STATS_COMMAND_LOOKBACK_DAYS"] = timedelta(
            days=stats_command_lookback_days.data,
        )

        return {"commands:stats:lookback-days"}

    @classmethod
    def _reload_stats_command_displayed_roles(cls, stats_command_displayed_roles: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the set of roles used to display statistics about.

        Returns the set of settings keys that have been changed.
        """
        STATS_COMMAND_DISPLAYED_ROLES_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or stats_command_displayed_roles != cls._most_recent_yaml["commands"][
                "stats"
            ]["displayed-roles"]
            or "STATS_COMMAND_DISPLAYED_ROLES" not in cls._settings,
        )
        if not STATS_COMMAND_DISPLAYED_ROLES_CHANGED:
            return set()

        cls._settings["STATS_COMMAND_DISPLAYED_ROLES"] = stats_command_displayed_roles.data

        return {"commands:stats:displayed-roles"}

    @classmethod
    def _reload_strike_command_timeout_duration(cls, strike_command_timeout_duration: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the duration to use when applying a timeout action for a strike increase.

        Returns the set of settings keys that have been changed.
        """
        STRIKE_COMMAND_TIMEOUT_DURATION_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or strike_command_timeout_duration != cls._most_recent_yaml["commands"][
                "strike"
            ]["timeout-duration"]
            or "STRIKE_COMMAND_TIMEOUT_DURATION" not in cls._settings,
        )
        if not STRIKE_COMMAND_TIMEOUT_DURATION_CHANGED:
            return set()

        cls._settings["STRIKE_COMMAND_TIMEOUT_DURATION"] = strike_command_timeout_duration.data

        return {"commands:strike:timeout-duration"}

    @classmethod
    def _reload_strike_performed_manually_warning_location(cls, strike_performed_manually_warning_location: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the location to send warning messages when strikes are performed manually.

        Returns the set of settings keys that have been changed.
        """
        STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or strike_performed_manually_warning_location != cls._most_recent_yaml["commands"][
                "strike"
            ]["performed-manually-warning-location"]
            or "STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION" not in cls._settings,
        )
        if not STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION_CHANGED:
            return set()

        cls._settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"] = (
            strike_performed_manually_warning_location.data
        )

        return {"commands:strike:performed-manually-warning-location"}

    @classmethod
    def _reload_messages_locale_code(cls, messages_locale_code: YAML) -> set[str]:  # type: ignore[misc]
        """
        Reload the selected locale for messages to be sent in.

        Returns the set of settings keys that have been changed.
        """
        MESSAGES_LOCALE_CODE_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or messages_locale_code != cls._most_recent_yaml["messages-locale-code"]
            or "MESSAGES_LOCALE_CODE" not in cls._settings,
        )
        if not MESSAGES_LOCALE_CODE_CHANGED:
            return set()

        cls._settings["MESSAGES_LOCALE_CODE"] = messages_locale_code.data

        return {"messages-locale-code"}

    @classmethod
    def _reload_send_introduction_reminders_enabled(cls, send_introduction_reminders_enabled: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the flag for whether the "send-introduction-reminders" task is enabled.

        Returns the set of settings keys that have been changed.
        """
        SEND_INTRODUCTION_REMINDERS_ENABLED_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or send_introduction_reminders_enabled != cls._most_recent_yaml["reminders"][
                "send-introduction-reminders"
            ]["enabled"]
            or "SEND_INTRODUCTION_REMINDERS_ENABLED" not in cls._settings,
        )
        if not SEND_INTRODUCTION_REMINDERS_ENABLED_CHANGED:
            return set()

        cls._settings["SEND_INTRODUCTION_REMINDERS_ENABLED"] = (
            send_introduction_reminders_enabled.data
        )

        return {"reminders:send-introduction-reminders:enabled"}

    @classmethod
    def _reload_send_introduction_reminders_delay(cls, send_introduction_reminders_delay: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the amount of time to wait before sending introduction-reminders to a user.

        Returns the set of settings keys that have been changed.

        Waiting begins from the time that the user joined your community group's Discord guild.
        """
        SEND_INTRODUCTION_REMINDERS_DELAY_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or send_introduction_reminders_delay != cls._most_recent_yaml["reminders"][
                "send-introduction-reminders"
            ]["delay"]
            or "SEND_INTRODUCTION_REMINDERS_DELAY" not in cls._settings,
        )
        if not SEND_INTRODUCTION_REMINDERS_DELAY_CHANGED:
            return set()

        cls._settings["SEND_INTRODUCTION_REMINDERS_DELAY"] = (
            send_introduction_reminders_delay.data
        )

        return {"reminders:send-introduction-reminders:delay"}

    @classmethod
    def _reload_send_introduction_reminders_interval(cls, send_introduction_reminders_interval: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the interval of time between executing the task to send introduction-reminders.

        Returns the set of settings keys that have been changed.
        """
        SEND_INTRODUCTION_REMINDERS_INTERVAL_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or send_introduction_reminders_interval != cls._most_recent_yaml["reminders"][
                "send-introduction-reminders"
            ]["interval"]
            or "SEND_INTRODUCTION_REMINDERS_INTERVAL_SECONDS" not in cls._settings,
        )
        if not SEND_INTRODUCTION_REMINDERS_INTERVAL_CHANGED:
            return set()

        cls._settings["SEND_INTRODUCTION_REMINDERS_INTERVAL_SECONDS"] = (
            send_introduction_reminders_interval.data.total_seconds()
        )

        return {"reminders:send-introduction-reminders:interval"}

    @classmethod
    def _reload_send_get_roles_reminders_enabled(cls, send_get_roles_reminders_enabled: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the flag for whether the "send-get-roles-reminders" task is enabled.

        Returns the set of settings keys that have been changed.
        """
        SEND_GET_ROLES_REMINDERS_ENABLED_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or send_get_roles_reminders_enabled != cls._most_recent_yaml["reminders"][
                "send-get-roles-reminders"
            ]["enabled"]
            or "SEND_GET_ROLES_REMINDERS_ENABLED" not in cls._settings,
        )
        if not SEND_GET_ROLES_REMINDERS_ENABLED_CHANGED:
            return set()

        cls._settings["SEND_GET_ROLES_REMINDERS_ENABLED"] = (
            send_get_roles_reminders_enabled.data
        )

        return {"reminders:send-get-roles-reminders:enabled"}

    @classmethod
    def _reload_send_get_roles_reminders_delay(cls, send_get_roles_reminders_delay: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the amount of time to wait before sending get-roles-reminders to a user.

        Returns the set of settings keys that have been changed.

        Waiting begins from the time that the user was inducted as a guest
        into your community group's Discord guild.
        """
        SEND_GET_ROLES_REMINDERS_DELAY_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or send_get_roles_reminders_delay != cls._most_recent_yaml["reminders"][
                "send-get-roles-reminders"
            ]["delay"]
            or "SEND_GET_ROLES_REMINDERS_DELAY" not in cls._settings,
        )
        if not SEND_GET_ROLES_REMINDERS_DELAY_CHANGED:
            return set()

        cls._settings["SEND_GET_ROLES_REMINDERS_DELAY"] = (
            send_get_roles_reminders_delay.data
        )

        return {"reminders:send-get-roles-reminders:delay"}

    @classmethod
    def _reload_send_get_roles_reminders_interval(cls, send_get_roles_reminders_interval: YAML) -> set[str]:  # type: ignore[misc] # noqa: E501
        """
        Reload the interval of time between executing the task to send get-roles-reminders.

        Returns the set of settings keys that have been changed.
        """
        SEND_GET_ROLES_REMINDERS_INTERVAL_CHANGED: Final[bool] = bool(
            cls._most_recent_yaml is None
            or send_get_roles_reminders_interval != cls._most_recent_yaml["reminders"][
                "send-get-roles-reminders"
            ]["interval"]
            or "SEND_GET_ROLES_REMINDERS_INTERVAL_SECONDS" not in cls._settings,
        )
        if not SEND_GET_ROLES_REMINDERS_INTERVAL_CHANGED:
            return set()

        cls._settings["SEND_GET_ROLES_REMINDERS_INTERVAL_SECONDS"] = (
            send_get_roles_reminders_interval.data.total_seconds()
        )

        return {"reminders:send-get-roles-reminders:interval"}


# TODO: Move to change_config cog

def _get_scalar_config_setting_value(config_setting_name: str, yaml_settings_tree: YAML) -> str | None:  # noqa: E501
    single_yaml_scalar_setting: YAML | None = yaml_settings_tree.get(config_setting_name, None)

    if single_yaml_scalar_setting is None:
        return single_yaml_scalar_setting

    CONFIG_SETTING_HAS_VALID_TYPE: Final[bool] = bool(
        not single_yaml_scalar_setting.is_mapping()
        and (
            single_yaml_scalar_setting.is_scalar()
            or single_yaml_scalar_setting.is_sequence()
        )  # noqa: COM812
    )
    if not CONFIG_SETTING_HAS_VALID_TYPE:
        MAPPING_TYPE_MESSAGE: Final[str] = "Got config mapping when scalar expected."
        raise RuntimeError(MAPPING_TYPE_MESSAGE)

    scalar_config_setting_value: object = single_yaml_scalar_setting.validator.to_yaml(
        single_yaml_scalar_setting.data,
    )

    if isinstance(scalar_config_setting_value, str):
        if not single_yaml_scalar_setting.is_scalar():
            SCALAR_TYPE_MESSAGE: Final[str] = "Got invalid config type when scalar expected."
            raise RuntimeError(SCALAR_TYPE_MESSAGE)

        return scalar_config_setting_value

    if isinstance(scalar_config_setting_value, Iterable):
        if not single_yaml_scalar_setting.is_sequence():
            SEQUENCE_TYPE_MESSAGE: Final[str] = (
                "Got invalid config type when sequence expected."
            )
            raise RuntimeError(SEQUENCE_TYPE_MESSAGE)

        if not all(inner_value.is_scalar() for inner_value in single_yaml_scalar_setting):
            ONLY_SCALAR_SEQUENCES_SUPPORTED_MESSAGE: Final[str] = (
                "Only sequences of scalars are currently supported "
                "to be used in configuration."
            )
            raise NotImplementedError(ONLY_SCALAR_SEQUENCES_SUPPORTED_MESSAGE)

        return ",".join(scalar_config_setting_value)

    raise NotImplementedError


def _get_mapping_config_setting_value(partial_config_setting_name: str, partial_yaml_settings_tree: YAML) -> str | None:  # noqa: E501
    if ":" not in partial_config_setting_name:
        return _get_scalar_config_setting_value(
            partial_config_setting_name,
            partial_yaml_settings_tree,
        )

    key: str
    remainder: str
    key, _, remainder = partial_config_setting_name.partition(":")

    single_yaml_mapping_setting: YAML | None = partial_yaml_settings_tree.get(key, None)

    if single_yaml_mapping_setting is not None and single_yaml_mapping_setting.is_mapping():
        return _get_mapping_config_setting_value(remainder, single_yaml_mapping_setting)

    return _get_scalar_config_setting_value(
        partial_config_setting_name,
        partial_yaml_settings_tree,
    )


def view_single_config_setting_value(config_setting_name: str, settings_accessor: SettingsAccessor) -> str | None:  # noqa: E501
    """Return the value of a single configuration setting from the setting tree hierarchy."""
    # noinspection PyProtectedMember
    current_yaml: YAML | None = settings_accessor._most_recent_yaml  # noqa: SLF001
    if current_yaml is None:
        YAML_NOT_LOADED_MESSAGE: Final[str] = (
            "Invalid state: Config YAML has not yet been loaded."
        )
        raise RuntimeError(YAML_NOT_LOADED_MESSAGE)

    # noinspection PyProtectedMember
    return _get_mapping_config_setting_value(config_setting_name, current_yaml)


def _set_scalar_or_sequence_config_setting_value(config_setting_name: str, new_config_setting_value: str, yaml_settings_tree: YAML) -> YAML:  # noqa: E501
    if config_setting_name not in yaml_settings_tree:
        yaml_settings_tree[config_setting_name] = new_config_setting_value
        return yaml_settings_tree

    if yaml_settings_tree[config_setting_name].is_mapping():
        INVALID_MAPPING_CONFIG_TYPE_MESSAGE: Final[str] = (
            "Got incongruent YAML object. Expected sequence or scalar, got mapping."
        )
        raise TypeError(INVALID_MAPPING_CONFIG_TYPE_MESSAGE)

    if yaml_settings_tree[config_setting_name].is_scalar():
        yaml_settings_tree[config_setting_name] = new_config_setting_value
        return yaml_settings_tree

    if yaml_settings_tree[config_setting_name].is_sequence():
        yaml_settings_tree[config_setting_name] = [
            sequence_value.strip()
            for sequence_value
            in new_config_setting_value.strip().split(",")
        ]
        return yaml_settings_tree

    UNKNOWN_CONFIG_TYPE_MESSAGE: Final[str] = (
        "Unknown YAML object type. Expected sequence or scalar."
    )
    raise RuntimeError(UNKNOWN_CONFIG_TYPE_MESSAGE)


def _set_mapping_config_setting_value(partial_config_setting_name: str, new_config_setting_value: str, partial_yaml_settings_tree: YAML) -> YAML:  # noqa: E501
    if ":" not in partial_config_setting_name:
        return _set_scalar_or_sequence_config_setting_value(
            partial_config_setting_name,
            new_config_setting_value,
            partial_yaml_settings_tree,
        )

    key: str
    remainder: str
    key, _, remainder = partial_config_setting_name.partition(":")

    if key not in partial_yaml_settings_tree:
        partial_yaml_settings_tree[key] = _set_required_value_from_validator_config(
            remainder if ":" in partial_config_setting_name else None,
            new_config_setting_value,
            partial_yaml_settings_tree.validator.get_validator(key),
        )
        return partial_yaml_settings_tree

    if partial_yaml_settings_tree[key].is_mapping():
        partial_yaml_settings_tree[key] = _set_mapping_config_setting_value(
            remainder,
            new_config_setting_value,
            partial_yaml_settings_tree[key],
        )
        return partial_yaml_settings_tree

    return _set_scalar_or_sequence_config_setting_value(
        partial_config_setting_name,
        new_config_setting_value,
        partial_yaml_settings_tree,
    )


def _set_required_value_from_validator_config(partial_config_setting_name: str | None, new_config_setting_value: str, yaml_validator: strictyaml.Validator) -> "NestedMapping | str | Sequence[str]":  # noqa: E501
    VALIDATOR_IS_SCALAR_TYPE: Final[bool] = bool(
        isinstance(yaml_validator, strictyaml.ScalarValidator)
        and (partial_config_setting_name is None or ":" not in partial_config_setting_name)  # noqa: COM812
    )
    if VALIDATOR_IS_SCALAR_TYPE:
        return new_config_setting_value

    VALIDATOR_IS_SEQUENCE_TYPE: Final[bool] = bool(
        isinstance(yaml_validator, strictyaml.validators.SeqValidator)
        and (partial_config_setting_name is None or ":" not in partial_config_setting_name)  # noqa: COM812
    )
    if VALIDATOR_IS_SEQUENCE_TYPE:
        return [
            sequence_value.strip()
            for sequence_value
            in new_config_setting_value.strip().split(",")
        ]

    VALIDATOR_IS_MAPPING_TYPE: Final[bool] = bool(
        isinstance(yaml_validator, strictyaml.validators.MapValidator)
        and hasattr(yaml_validator, "_required_keys")
        and partial_config_setting_name is not None  # noqa: COM812
    )
    if VALIDATOR_IS_MAPPING_TYPE:
        key: str
        remainder: str
        key, _, remainder = partial_config_setting_name.partition(":")  # type: ignore[union-attr]

        # noinspection PyProtectedMember,PyUnresolvedReferences
        if set(yaml_validator._required_keys) - {key}:  # noqa: SLF001
            raise ChangingSettingWithRequiredSiblingError

        # noinspection PyUnresolvedReferences
        return {
            key: _set_required_value_from_validator_config(  # type: ignore[dict-item]
                remainder if ":" in partial_config_setting_name else None,  # type: ignore[operator]
                new_config_setting_value,
                yaml_validator.get_validator(key),
            ),
        }

    UNKNOWN_CONFIG_TYPE_MESSAGE: Final[str] = (
        "Unknown YAML validator type. Expected mapping, sequence or scalar."
    )
    raise RuntimeError(UNKNOWN_CONFIG_TYPE_MESSAGE)


def assign_single_config_setting_value(config_setting_name: str, new_config_setting_value: str, settings_accessor: SettingsAccessor) -> None:  # noqa: E501
    """Set the value of a single configuration setting within the setting tree hierarchy."""
    # noinspection PyProtectedMember
    current_yaml: YAML | None = settings_accessor._most_recent_yaml  # noqa: SLF001
    if current_yaml is None:
        YAML_NOT_LOADED_MESSAGE: Final[str] = (
            "Invalid state: Config YAML has not yet been loaded."
        )
        raise RuntimeError(YAML_NOT_LOADED_MESSAGE)

    config_setting_error: ChangingSettingWithRequiredSiblingError
    try:
        settings_accessor = _set_mapping_config_setting_value(
            config_setting_name,
            new_config_setting_value,
            current_yaml,
        )
    except ChangingSettingWithRequiredSiblingError as config_setting_error:
        raise type(config_setting_error)(
            config_setting_name=config_setting_name,
        ) from config_setting_error

    print(settings_accessor.as_yaml())

    # TODO: save yaml
