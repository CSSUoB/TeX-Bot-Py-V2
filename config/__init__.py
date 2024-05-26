"""
Contains settings values and import & setup functions.

Settings values are imported from the .env file or the current environment variables.
These values are used to configure the functionality of the bot at run-time.
"""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "PROJECT_ROOT",
    "TRANSLATED_MESSAGES_LOCALE_CODES",
    "LogLevels",
    "run_setup",
    "settings",
    "check_for_deprecated_environment_variables",
)


import contextlib
import importlib
import logging
import os
from collections.abc import Iterable
from logging import Logger
from typing import Final

from exceptions import BotRequiresRestartAfterConfigChange

from ._settings import SettingsAccessor
from .constants import (
    PROJECT_ROOT,
    TRANSLATED_MESSAGES_LOCALE_CODES,
    LogLevels,
)

logger: Final[Logger] = logging.getLogger("TeX-Bot")

settings: Final[SettingsAccessor] = SettingsAccessor()


def run_setup() -> None:
    """Execute the setup functions required, before other modules can be run."""
    check_for_deprecated_environment_variables()

    with contextlib.suppress(BotRequiresRestartAfterConfigChange):
        settings.reload()

    # TODO: load messages here using language from settings

    logger.debug("Begin database setup")

    importlib.import_module("db")
    from django.core import management

    management.call_command("migrate")

    logger.debug("Database setup completed")


def check_for_deprecated_environment_variables() -> None:
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


# @classmethod
# @functools.lru_cache(maxsize=5)
# def _get_messages_dict(cls, raw_messages_file_path: str | None) -> Mapping[str, object]:
#     JSON_DECODING_ERROR_MESSAGE: Final[str] = (
#         "Messages JSON file must contain a JSON string that can be decoded "
#         "into a Python dict object."
#     )
#
#     messages_file_path: Path = (
#         Path(raw_messages_file_path)
#         if raw_messages_file_path
#         else PROJECT_ROOT / Path("messages.json")
#     )
#
#     if not messages_file_path.is_file():
#         MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE: Final[str] = (
#             "MESSAGES_FILE_PATH must be a path to a file that exists."
#         )
#         raise ImproperlyConfiguredError(MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE)
#
#     messages_file: IO[str]
#     with messages_file_path.open(encoding="utf8") as messages_file:
#         e: json.JSONDecodeError
#         try:
#             messages_dict: object = json.load(messages_file)
#         except json.JSONDecodeError as e:
#             raise ImproperlyConfiguredError(JSON_DECODING_ERROR_MESSAGE) from e
#
#     if not isinstance(messages_dict, Mapping):
#         raise ImproperlyConfiguredError(JSON_DECODING_ERROR_MESSAGE)
#
#     return messages_dict
#
# @classmethod
# def _setup_welcome_messages(cls) -> None:
#     messages_dict: Mapping[str, object] = cls._get_messages_dict(
#         os.getenv("MESSAGES_FILE_PATH"),
#     )
#
#     if "welcome_messages" not in messages_dict:
#         raise MessagesJSONFileMissingKeyError(missing_key="welcome_messages")
#
#     WELCOME_MESSAGES_KEY_IS_VALID: Final[bool] = bool(
#         isinstance(messages_dict["welcome_messages"], Iterable)
#         and messages_dict["welcome_messages"],
#     )
#     if not WELCOME_MESSAGES_KEY_IS_VALID:
#         raise MessagesJSONFileValueError(
#             dict_key="welcome_messages",
#             invalid_value=messages_dict["welcome_messages"],
#         )
#
#     cls._settings["WELCOME_MESSAGES"] = set(messages_dict["welcome_messages"])  # type: ignore[call-overload]
#
# @classmethod
# def _setup_roles_messages(cls) -> None:
#     messages_dict: Mapping[str, object] = cls._get_messages_dict(
#         os.getenv("MESSAGES_FILE_PATH"),
#     )
#
#     if "roles_messages" not in messages_dict:
#         raise MessagesJSONFileMissingKeyError(missing_key="roles_messages")
#
#     ROLES_MESSAGES_KEY_IS_VALID: Final[bool] = (
#         isinstance(messages_dict["roles_messages"], Iterable)
#         and bool(messages_dict["roles_messages"])
#     )
#     if not ROLES_MESSAGES_KEY_IS_VALID:
#         raise MessagesJSONFileValueError(
#             dict_key="roles_messages",
#             invalid_value=messages_dict["roles_messages"],
#         )
#     cls._settings["ROLES_MESSAGES"] = set(messages_dict["roles_messages"])  # type: ignore[call-overload]
