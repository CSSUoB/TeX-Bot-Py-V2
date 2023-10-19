"""
Contains settings values and import & setup functions.

Settings values are imported from the .env file or the current environment variables.
These values are used to configure the functionality of the bot at run-time.
"""

import json
import logging
import os
import re
from collections.abc import Callable, Sequence
from datetime import timedelta
from pathlib import Path
from re import Match
from typing import Any, Final

import django
import dotenv
import validators

from exceptions import (
    ImproperlyConfigured,
    MessagesJSONFileMissingKey,
    MessagesJSONFileValueError,
)

TRUE_VALUES: Final[frozenset[str]] = frozenset({"true", "1", "t", "y", "yes", "on"})
FALSE_VALUES: Final[frozenset[str]] = frozenset({"false", "0", "f", "n", "no", "off"})
VALID_SEND_INTRODUCTION_REMINDERS_VALUES: Final[frozenset[str]] = frozenset(
    {"once"} | TRUE_VALUES | FALSE_VALUES
)
DEFAULT_STATISTICS_ROLES: Final[frozenset[str]] = frozenset(
    {
        "Committee",
        "Committee-Elect",
        "Student Rep",
        "Member",
        "Guest",
        "Server Booster",
        "Foundation Year",
        "First Year",
        "Second Year",
        "Final Year",
        "Year In Industry",
        "Year Abroad",
        "PGT",
        "PGR",
        "Alumnus/Alumna",
        "Postdoc",
        "Quiz Victor"
    }
)
LOG_LEVEL_CHOICES: Final[Sequence[str]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL"
)


class Settings:
    """
    Settings class that provides access to all settings values.

    Settings values can be accessed via key (like a dictionary) or via class attribute.
    """

    _instance: "Settings | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "Settings":
        """
        Return the singleton settings container instance.

        If no singleton instance exists, a new one is created, then stored as a class variable.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(self) -> None:
        """Instantiate a new settings container with False is_setup flags."""
        self._is_env_variables_setup: bool = False
        self._is_django_setup: bool = False
        self._settings: dict[str, Any] = {}

    def __getattr__(self, item: str) -> Any:
        """Retrieve settings value by attribute lookup."""
        self._setup_env_variables()

        if item in self._settings:
            return self._settings[item]

        if re.match(r"\A[A-Z](?:[A-Z_]*[A-Z])?\Z", item):
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = f"{item!r} is not a valid settings key."
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )
        raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

    def __getitem__(self, item: str) -> Any:
        """Retrieve settings value by key lookup."""
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item) from None

    def _setup_env_variables(self) -> None:  # noqa: C901, PLR0912
        """
        Load environment values into the settings dictionary.

        Environment values are loaded from the .env file/the current environment variables and
        are only stored after the input values have been validated.
        """
        if not self._is_env_variables_setup:
            dotenv.load_dotenv()

            discord_bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
            discord_bot_token_is_valid: bool = bool(
                bool(discord_bot_token)
                and bool(
                    re.match(
                        r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z",
                        discord_bot_token
                    )
                )
            )
            if not discord_bot_token_is_valid:
                INVALID_BOT_TOKEN_MESSAGE: Final[str] = (
                    "DISCORD_BOT_TOKEN must be a valid Discord bot token"
                    " (see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)."
                )
                raise ImproperlyConfigured(INVALID_BOT_TOKEN_MESSAGE)
            self._settings["DISCORD_BOT_TOKEN"] = discord_bot_token

            discord_guild_id: str = os.getenv("DISCORD_GUILD_ID", "")
            if not discord_guild_id or not re.match(r"\A\d{17,20}\Z", discord_guild_id):
                INVALID_GUILD_ID_MESSAGE: Final[str] = (
                    "DISCORD_GUILD_ID must be a valid Discord guild ID"
                    " (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)."
                )
                raise ImproperlyConfigured(INVALID_GUILD_ID_MESSAGE)
            self._settings["DISCORD_GUILD_ID"] = int(discord_guild_id)

            self._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = os.getenv(
                "DISCORD_LOG_CHANNEL_WEBHOOK_URL",
                ""
            )
            discord_log_channel_webhook_url_not_valid: bool = (
                self._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]
                and not (
                    validators.url(self._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"])
                    and self._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"].startswith(
                        "https://discord.com/api/webhooks/"
                    )
                )
            )
            if discord_log_channel_webhook_url_not_valid:
                INVALID_WEBHOOK_URL_MESSAGE: Final[str] = (
                    "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL"
                    " that points to a discord channel where logs should be displayed."
                )
                raise ImproperlyConfigured(INVALID_WEBHOOK_URL_MESSAGE)

            try:
                self._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = 100 * float(
                    os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01")
                )
            except ValueError as ping_command_easter_egg_probability_error:
                PROBABILITY_IS_NOT_FLOAT_MESSAGE: Final[str] = (
                    "PING_COMMAND_EASTER_EGG_PROBABILITY must be a float."
                )
                raise ImproperlyConfigured(
                    PROBABILITY_IS_NOT_FLOAT_MESSAGE
                ) from ping_command_easter_egg_probability_error
            if not 100 >= self._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] >= 0:
                PROBABILITY_IS_NOT_IN_RANGE_MESSAGE: Final[str] = (
                    "PING_COMMAND_EASTER_EGG_PROBABILITY must be a value"
                    " between & including 1 & 0."
                )
                raise ImproperlyConfigured(PROBABILITY_IS_NOT_IN_RANGE_MESSAGE)

            messages_file_path: Path = Path(os.getenv("MESSAGES_FILE_PATH", "messages.json"))
            if not messages_file_path.is_file():
                NO_FILE_PATH_MESSAGE: Final[str] = (
                    "MESSAGES_FILE_PATH must be a path to a file that exists."
                )
                raise ImproperlyConfigured(NO_FILE_PATH_MESSAGE)
            if messages_file_path.suffix != ".json":
                NOT_JSON_FILE_MESSAGE: Final[str] = (
                    "MESSAGES_FILE_PATH must be a path to a JSON file."
                )
                raise ImproperlyConfigured(NOT_JSON_FILE_MESSAGE)

            with messages_file_path.open(encoding="utf8") as messages_file:
                try:
                    messages_dict: dict[Any, Any] = json.load(messages_file)
                except json.JSONDecodeError as messages_file_error:
                    JSON_DECODING_ERROR_MESSAGE: Final[str] = (
                        "Messages JSON file must contain a JSON string that can be decoded"
                        " into a Python dict object."
                    )
                    raise ImproperlyConfigured(
                        JSON_DECODING_ERROR_MESSAGE
                    ) from messages_file_error

            if "welcome_messages" not in messages_dict:
                raise MessagesJSONFileMissingKey(missing_key="welcome_messages")
            welcome_messages_key_is_valid: bool = (
                    isinstance(messages_dict["welcome_messages"], list)
                    and bool(messages_dict["welcome_messages"])
            )
            if not welcome_messages_key_is_valid:
                raise MessagesJSONFileValueError(
                    dict_key="welcome_messages",
                    invalid_value=messages_dict["welcome_messages"]
                )
            self._settings["WELCOME_MESSAGES"] = messages_dict["welcome_messages"]

            if "roles_messages" not in messages_dict:
                raise MessagesJSONFileMissingKey(missing_key="roles_messages")
            roles_messages_key_is_valid: bool = (
                    isinstance(messages_dict["roles_messages"], list)
                    and bool(messages_dict["roles_messages"])
            )
            if not roles_messages_key_is_valid:
                raise MessagesJSONFileValueError(
                    dict_key="roles_messages",
                    invalid_value=messages_dict["roles_messages"]
                )
            self._settings["ROLES_MESSAGES"] = messages_dict["roles_messages"]

            self._settings["MEMBERS_PAGE_URL"] = os.getenv("MEMBERS_PAGE_URL", "")
            members_page_url_is_valid: bool = (
                    self._settings["MEMBERS_PAGE_URL"]
                    and validators.url(self._settings["MEMBERS_PAGE_URL"])
            )
            if not members_page_url_is_valid:
                INVALID_MEMBERS_PAGE_URL_MESSAGE: Final[str] = (
                    "MEMBERS_PAGE_URL must be a valid URL."
                )
                raise ImproperlyConfigured(INVALID_MEMBERS_PAGE_URL_MESSAGE)

            self._settings["MEMBERS_PAGE_COOKIE"] = os.getenv("MEMBERS_PAGE_COOKIE", "")
            members_page_cookie_is_valid: bool = (
                bool(self._settings["MEMBERS_PAGE_COOKIE"])
                and bool(
                    re.match(
                        r"\A[A-Fa-f\d]{128,256}\Z",
                        self._settings["MEMBERS_PAGE_COOKIE"]
                    )
                )
            )
            if not members_page_cookie_is_valid:
                INVALID_MEMBERS_PAGE_COOKIE_MESSAGE: Final[str] = (
                    "MEMBERS_PAGE_COOKIE must be a valid .ASPXAUTH cookie."
                )
                raise ImproperlyConfigured(INVALID_MEMBERS_PAGE_COOKIE_MESSAGE)

            send_introduction_reminders: str = str(
                os.getenv("SEND_INTRODUCTION_REMINDERS", "Once")
            ).lower()
            if send_introduction_reminders not in VALID_SEND_INTRODUCTION_REMINDERS_VALUES:
                INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE: Final[str] = (
                    "SEND_INTRODUCTION_REMINDERS must be one of:"
                    " \"Once\", \"Interval\" or \"False\"."
                )
                raise ImproperlyConfigured(INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE)
            if send_introduction_reminders in ("once", "interval"):
                self._settings["SEND_INTRODUCTION_REMINDERS"] = send_introduction_reminders
            elif send_introduction_reminders in TRUE_VALUES:
                self._settings["SEND_INTRODUCTION_REMINDERS"] = "once"
            else:
                self._settings["SEND_INTRODUCTION_REMINDERS"] = False

            introduction_reminder_interval: Match[str] | None = re.match(
                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
                str(os.getenv("INTRODUCTION_REMINDER_INTERVAL", "6h"))
            )
            self._settings["INTRODUCTION_REMINDER_INTERVAL"] = {"hours": 6}
            if self._settings["SEND_INTRODUCTION_REMINDERS"]:
                if not introduction_reminder_interval:
                    INVALID_INTRODUCTION_REMINDER_INTERVAL_MESSAGE: Final[str] = (
                        "INTRODUCTION_REMINDER_INTERVAL must contain the interval"
                        " in any combination of seconds, minutes or hours."
                    )
                    raise ImproperlyConfigured(INVALID_INTRODUCTION_REMINDER_INTERVAL_MESSAGE)
                self._settings["INTRODUCTION_REMINDER_INTERVAL"] = {
                    key: float(value)
                    for key, value
                    in introduction_reminder_interval.groupdict().items()
                    if value
                }

            kick_no_introduction_members: str = str(
                os.getenv("KICK_NO_INTRODUCTION_MEMBERS", "False")
            ).lower()
            if kick_no_introduction_members not in TRUE_VALUES | FALSE_VALUES:
                INVALID_KICK_NO_INTRODUCTION_MEMBERS_MESSAGE: Final[str] = (
                    "KICK_NO_INTRODUCTION_MEMBERS must be a boolean value."
                )
                raise ImproperlyConfigured(INVALID_KICK_NO_INTRODUCTION_MEMBERS_MESSAGE)
            self._settings["KICK_NO_INTRODUCTION_MEMBERS"] = (
                    kick_no_introduction_members in TRUE_VALUES
            )

            kick_no_introduction_members_delay: Match[str] | None = re.match(
                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
                str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS_DELAY", "5d"))
            )
            self._settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = timedelta()
            if self._settings["KICK_NO_INTRODUCTION_MEMBERS"]:
                if not kick_no_introduction_members_delay:
                    INVALID_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE: Final[str] = (
                        "KICK_NO_INTRODUCTION_MEMBERS_DELAY must contain the delay"
                        " in any combination of seconds, minutes, hours, days or weeks."
                    )
                    raise ImproperlyConfigured(
                        INVALID_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE
                    )
                self._settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = timedelta(
                    **{
                        key: float(value)
                        for key, value
                        in kick_no_introduction_members_delay.groupdict().items()
                        if value
                    }
                )
                if self._settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] <= timedelta(days=1):
                    TOO_SMALL_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE: Final[str] = (
                        "KICK_NO_INTRODUCTION_MEMBERS_DELAY must be greater than 1 day."
                    )
                    raise ImproperlyConfigured(
                        TOO_SMALL_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE
                    )

            send_get_roles_reminders: str = str(
                os.getenv("SEND_GET_ROLES_REMINDERS", "True")
            ).lower()
            if send_get_roles_reminders not in TRUE_VALUES | FALSE_VALUES:
                INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE: Final[str] = (
                    "SEND_GET_ROLES_REMINDERS must be a boolean value."
                )
                raise ImproperlyConfigured(INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE)
            self._settings["SEND_GET_ROLES_REMINDERS"] = (
                    send_get_roles_reminders in TRUE_VALUES
            )

            get_roles_reminder_interval: Match[str] | None = re.match(
                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
                str(os.getenv("GET_ROLES_REMINDER_INTERVAL", "24h"))
            )
            self._settings["GET_ROLES_REMINDER_INTERVAL"] = {"hours": 24}
            if self._settings["SEND_GET_ROLES_REMINDERS"]:
                if not get_roles_reminder_interval:
                    INVALID_GET_ROLES_REMINDER_INTERVAL_MESSAGE: Final[str] = (
                        "GET_ROLES_REMINDER_INTERVAL must contain the interval"
                        " in any combination of seconds, minutes or hours."
                    )
                    raise ImproperlyConfigured(INVALID_GET_ROLES_REMINDER_INTERVAL_MESSAGE)
                self._settings["GET_ROLES_REMINDER_INTERVAL"] = {
                    key: float(value)
                    for key, value
                    in get_roles_reminder_interval.groupdict().items()
                    if value
                }

            try:
                statistics_days: float = float(os.getenv("STATISTICS_DAYS", "30"))
            except ValueError as statistics_days_error:
                INVALID_STATISTICS_DAYS_MESSAGE: Final[str] = (
                    "STATISTICS_DAYS must contain the statistics period in days."
                )
                raise ImproperlyConfigured(
                    INVALID_STATISTICS_DAYS_MESSAGE
                ) from statistics_days_error
            self._settings["STATISTICS_DAYS"] = timedelta(days=statistics_days)

            self._settings["STATISTICS_ROLES"] = set(
                filter(None, os.getenv("STATISTICS_ROLES", "").split(","))
            ) or DEFAULT_STATISTICS_ROLES

            console_log_level: str = str(os.getenv("CONSOLE_LOG_LEVEL", "INFO")).upper()
            if console_log_level not in LOG_LEVEL_CHOICES:
                INVALID_LOG_LEVEL_MESSAGE: Final[str] = f"""LOG_LEVEL must be one of {
                    ",".join(f"{log_level_choice!r}"
                    for log_level_choice
                    in LOG_LEVEL_CHOICES[:-1])
                } or \"{LOG_LEVEL_CHOICES[-1]}\"."""
                raise ImproperlyConfigured(INVALID_LOG_LEVEL_MESSAGE)
            # noinspection SpellCheckingInspection
            logging.basicConfig(
                level=getattr(logging, console_log_level),
                format="%(levelname)s: %(message)s"
            )

            self._settings["MODERATION_DOCUMENT_URL"] = os.getenv(
                "MODERATION_DOCUMENT_URL", ""
            )
            moderation_document_url_is_valid: bool = (
                self._settings["MODERATION_DOCUMENT_URL"]
                and validators.url(self._settings["MODERATION_DOCUMENT_URL"])
            )
            if not moderation_document_url_is_valid:
                MODERATION_DOCUMENT_URL_MESSAGE: Final[str] = (
                    "MODERATION_DOCUMENT_URL must be a valid URL."
                )
                raise ImproperlyConfigured(MODERATION_DOCUMENT_URL_MESSAGE)

            self._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = os.getenv(
                "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION", "DM"
            )
            if not self._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"]:
                MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE: Final[str] = (
                    "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE must be a valid name"
                    " of a channel in the CSS Discord server."
                )
                raise ImproperlyConfigured(MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE)

            self._is_env_variables_setup = True

    def _setup_django(self) -> None:
        """
        Load the correct settings module into the Django process.

        Model instances & database data cannot be accessed by cogs until
        Django's settings module has been loaded.
        """
        if not self._is_django_setup:
            os.environ["DJANGO_SETTINGS_MODULE"] = "db.settings"
            django.setup()

            self._is_django_setup = True


settings: Settings = Settings()
# noinspection PyProtectedMember
setup_env_variables: Callable[[], None] = settings._setup_env_variables  # noqa: SLF001
# noinspection PyProtectedMember
setup_django: Callable[[], None] = settings._setup_django  # noqa: SLF001
