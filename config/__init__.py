"""
Contains settings values and import & setup functions.

Settings values are imported from the .env file or the current environment variables.
These values are used to configure the functionality of the bot at run-time.
"""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "PROJECT_ROOT",
    "MESSAGES_LOCALE_CODES",
    "LogLevels",
    "run_setup",
    "settings",
    "check_for_deprecated_environment_variables",
    "messages",
    "CONFIG_SETTINGS_HELPS",
    "ConfigSettingHelp",
    "get_settings_file_path",
    "view_single_config_setting_value",
    "assign_single_config_setting_value",
)


import importlib
import logging
import os
from collections.abc import Iterable
from logging import Logger
from typing import Final

from asgiref.sync import async_to_sync

from ._messages import MessagesAccessor as _MessagesAccessor
from ._settings import SettingsAccessor as _SettingsAccessor
from ._settings import get_settings_file_path, utils
from .constants import (
    CONFIG_SETTINGS_HELPS,
    MESSAGES_LOCALE_CODES,
    PROJECT_ROOT,
    ConfigSettingHelp,
    LogLevels,
)

logger: Final[Logger] = logging.getLogger("TeX-Bot")

settings: Final[_SettingsAccessor] = _SettingsAccessor()
messages: Final[_MessagesAccessor] = _MessagesAccessor()


def run_setup() -> None:
    """Execute the setup functions required, before other modules can be run."""
    check_for_deprecated_environment_variables()

    async_to_sync(settings.reload)()
    async_to_sync(messages.load)(settings["MESSAGES_LOCALE_CODE"])

    logger.debug("Begin database setup")

    importlib.import_module("db")
    from django.core import management

    management.call_command("migrate")

    logger.debug("Database setup completed")


def check_for_deprecated_environment_variables() -> None:
    """Raise an error if the old method of configuration (environment variables) is used."""
    if utils.is_running_in_async():
        RUNNING_IN_ASYNC_MESSAGE: Final[str] = (
            "Cannot check for deprecated environment variables while TeX-Bot is running."
        )
        raise RuntimeError(RUNNING_IN_ASYNC_MESSAGE)

    CONFIGURATION_VIA_ENVIRONMENT_VARIABLES_IS_DEPRECATED_ERROR: Final[DeprecationWarning] = (
        DeprecationWarning(
            (
                "Configuration using environment variables is deprecated. "
                "Use a `tex-bot-deployment.yaml` file instead."
            ),
        )
    )

    if (PROJECT_ROOT / ".env").exists():
        raise CONFIGURATION_VIA_ENVIRONMENT_VARIABLES_IS_DEPRECATED_ERROR

    DEPRECATED_ENVIRONMENT_VARIABLE_NAMES: Final[Iterable[str]] = (
        "DISCORD_BOT_TOKEN",
        "BOT_TOKEN",
        "DISCORD_TOKEN",
        "DISCORD_GUILD_ID",
        "DISCORD_MAIN_GUILD_ID",
        "MAIN_GUILD_ID",
        "GUILD_ID",
        "DISCORD_LOG_CHANNEL_WEBHOOK_URL",
        "DISCORD_LOG_CHANNEL_WEBHOOK",
        "DISCORD_LOGGING_WEBHOOK_URL",
        "DISCORD_LOGGING_WEBHOOK",
        "DISCORD_LOG_CHANNEL_LOCATION",
        "GROUP_NAME",
        "GROUP_FULL_NAME",
        "GROUP_SHORT_NAME",
        "PURCHASE_MEMBERSHIP_URL",
        "PURCHASE_MEMBERSHIP_LINK",
        "PURCHASE_MEMBERSHIP_WEBSITE",
        "PURCHASE_MEMBERSHIP_INFO",
        "MEMBERSHIP_PERKS_URL",
        "MEMBERSHIP_PERKS_LINK",
        "MEMBERSHIP_PERKS",
        "MEMBERSHIP_PERKS_WEBSITE",
        "MEMBERSHIP_PERKS_INFO",
        "CONSOLE_LOG_LEVEL",
        "MEMBERS_LIST_URL",
        "MEMBERS_LIST_LIST",
        "MEMBERS_LIST",
        "MEMBERS_LIST_URL_SESSION_COOKIE",
        "MEMBERS_LIST_AUTH_SESSION_COOKIE",
        "MEMBERS_LIST_URL_AUTH_COOKIE",
        "MEMBERS_LIST_SESSION_COOKIE",
        "MEMBERS_LIST_URL_COOKIE",
        "MEMBERS_LIST_AUTH_COOKIE",
        "MEMBERS_LIST_COOKIE",
        "PING_COMMAND_EASTER_EGG_PROBABILITY",
        "PING_EASTER_EGG_PROBABILITY",
        "MESSAGES_FILE_PATH",
        "MESSAGES_FILE",
        "SEND_INTRODUCTION_REMINDERS",
        "SEND_INTRODUCTION_REMINDERS_DELAY",
        "SEND_INTRODUCTION_REMINDERS_INTERVAL",
        "SEND_GET_ROLES_REMINDERS",
        "SEND_GET_ROLES_REMINDERS_DELAY",
        "SEND_GET_ROLES_REMINDERS_INTERVAL",
        "ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL",
        "STATISTICS_DAYS",
        "STATISTICS_ROLES",
        "STATS_DAYS",
        "STATS_ROLES",
        "MODERATION_DOCUMENT_URL",
        "MODERATION_DOCUMENT_LINK",
        "MODERATION_DOCUMENT",
        "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION",
        "MANUAL_MODERATION_WARNING_LOCATION",
        "MANUAL_MODERATION_MESSAGE_LOCATION",
        "STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION",
        "STRIKE_PERFORMED_MANUALLY_WARNING_MESSAGE_LOCATION",
        "STRIKE_PERFORMED_MANUALLY_MESSAGE_LOCATION",
        "MANUAL_STRIKE_WARNING_MESSAGE_LOCATION",
        "MANUAL_STRIKE_MESSAGE_LOCATION",
        "MANUAL_STRIKE_WARNING_LOCATION",
    )
    deprecated_environment_variable_name: str
    for deprecated_environment_variable_name in DEPRECATED_ENVIRONMENT_VARIABLE_NAMES:
        deprecated_environment_variable_found: bool = bool(
            (
                deprecated_environment_variable_name.upper() in os.environ
                or deprecated_environment_variable_name.lower() in os.environ
                or f"TEX_BOT_{deprecated_environment_variable_name}".upper() in os.environ
                or f"TEX_BOT_{deprecated_environment_variable_name}".lower() in os.environ
            ),
        )
        if deprecated_environment_variable_found:
            raise CONFIGURATION_VIA_ENVIRONMENT_VARIABLES_IS_DEPRECATED_ERROR


def view_single_config_setting_value(config_setting_name: str) -> str | None:
    """Return the value of a single configuration setting from settings tree hierarchy."""
    return settings.view_single_raw_value(config_setting_name=config_setting_name)


async def assign_single_config_setting_value(config_setting_name: str, new_config_setting_value: str) -> None:  # noqa: E501
    """Set the value of a single configuration setting within settings tree hierarchy."""
    return await settings.assign_single_raw_value(
        config_setting_name=config_setting_name,
        new_config_setting_value=new_config_setting_value,
    )