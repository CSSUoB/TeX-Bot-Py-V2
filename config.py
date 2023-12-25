"""
Contains settings values and import & setup functions.

Settings values are imported from the .env file or the current environment variables.
These values are used to configure the functionality of the bot at run-time.
"""

import functools
import json
import logging
import os
import re
from collections.abc import Sequence, Mapping, Iterable
from datetime import timedelta
from pathlib import Path
from re import Match
from typing import Any, ClassVar, Final, Self, final, IO

import dotenv
import validators
from django.core import management

from exceptions import (
    ImproperlyConfiguredError,
    MessagesJSONFileMissingKeyError,
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


@final
class Settings:
    """
    Settings class that provides access to all settings values.

    Settings values can be accessed via key (like a dictionary) or via class attribute.
    """

    _instance: ClassVar[Self | None] = None

    @classmethod
    def get_invalid_settings_key_message(cls, item: str) -> str:
        return f"{item!r} is not a valid settings key."

    # noinspection PyTypeHints
    def __new__(cls, *args: object, **kwargs: object) -> Self:
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
        self._settings: dict[str, object] = {}

    def __getattr__(self, item: str) -> Any:
        """Retrieve settings value by attribute lookup."""
        if not self._is_env_variables_setup:
            self._setup_env_variables()

        if item in self._settings:
            return self._settings[item]

        if re.match(r"\A[A-Z](?:[A-Z_]*[A-Z])?\Z", item):
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = self.get_invalid_settings_key_message(
                item
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )
        raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

    def __getitem__(self, item: str) -> Any:
        """Retrieve settings value by key lookup."""
        e: AttributeError
        try:
            return getattr(self, item)
        except AttributeError as e:
            key_error_message: str = item

            if self.get_invalid_settings_key_message(item) in str(e):
                key_error_message = str(e)

            raise KeyError(key_error_message) from None

    @staticmethod
    def _setup_logging() -> None:
        raw_console_log_level: str = str(os.getenv("CONSOLE_LOG_LEVEL", "INFO")).upper()

        if raw_console_log_level not in LOG_LEVEL_CHOICES:
            INVALID_LOG_LEVEL_MESSAGE: Final[str] = f"""LOG_LEVEL must be one of {
                ",".join(f"{log_level_choice!r}"
                    for log_level_choice
                    in LOG_LEVEL_CHOICES[:-1])
                } or {LOG_LEVEL_CHOICES[-1]!r}."""
            raise ImproperlyConfiguredError(INVALID_LOG_LEVEL_MESSAGE)

        # noinspection SpellCheckingInspection
        logging.basicConfig(
            level=getattr(logging, raw_console_log_level),
            format="%(levelname)s: %(message)s"
        )

    def _setup_discord_bot_token(self) -> None:
        raw_discord_bot_token: str | None = os.getenv("DISCORD_BOT_TOKEN")

        DISCORD_BOT_TOKEN_IS_VALID: Final[bool] = bool(
            raw_discord_bot_token
            and re.match(
                r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z",
                raw_discord_bot_token
            )
        )
        if not DISCORD_BOT_TOKEN_IS_VALID:
            INVALID_DISCORD_BOT_TOKEN_MESSAGE: Final[str] = (
                "DISCORD_BOT_TOKEN must be a valid Discord bot token "
                "(see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_BOT_TOKEN_MESSAGE)

        self._settings["DISCORD_BOT_TOKEN"] = raw_discord_bot_token

    def _setup_discord_log_channel_webhook_url(self) -> None:
        raw_discord_log_channel_webhook_url: str = os.getenv(
           "DISCORD_LOG_CHANNEL_WEBHOOK_URL",
           ""
        )

        DISCORD_LOG_CHANNEL_WEBHOOK_URL_IS_VALID: Final[bool] = bool(
            not raw_discord_log_channel_webhook_url
            or (
                validators.url(raw_discord_log_channel_webhook_url)
                and raw_discord_log_channel_webhook_url.startswith(
                    "https://discord.com/api/webhooks/"
                )
            )
        )
        if not DISCORD_LOG_CHANNEL_WEBHOOK_URL_IS_VALID:
            INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE: Final[str] = (
                "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL "
                "that points to a discord channel where logs should be displayed."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE)

        self._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = raw_discord_log_channel_webhook_url

    def _setup_guild_id(self) -> None:
        raw_discord_guild_id: str | None = os.getenv("DISCORD_GUILD_ID")

        DISCORD_GUILD_ID_IS_VALID: Final[bool] = bool(
            raw_discord_guild_id
            and re.match(r"\A\d{17,20}\Z", raw_discord_guild_id)
        )
        if not DISCORD_GUILD_ID_IS_VALID:
            INVALID_DISCORD_GUILD_ID_MESSAGE: Final[str] = (
                "DISCORD_GUILD_ID must be a valid Discord guild ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_GUILD_ID_MESSAGE)

        self._settings["DISCORD_GUILD_ID"] = int(raw_discord_guild_id)

    def _setup_ping_command_easter_egg_probability(self) -> None:
        INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE: Final[str] = (
            "PING_COMMAND_EASTER_EGG_PROBABILITY must be a float between & including 1 & 0."
        )

        e: ValueError
        try:
            raw_ping_command_easter_egg_probability: float = 100 * float(
                os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01")
            )
        except ValueError as e:
            raise (
                ImproperlyConfiguredError(INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE)
            ) from e

        if not 0 <= raw_ping_command_easter_egg_probability <= 100:
            raise ImproperlyConfiguredError(
                INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE
            )

        self._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
            raw_ping_command_easter_egg_probability
        )

    @staticmethod
    @functools.lru_cache(maxsize=5)
    def _get_messages_dict(messages_file_path: Path | None) -> Mapping[str, object]:
        if not messages_file_path:
            messages_file_path = Path("messages.json")

        if not messages_file_path.is_file():
            MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE: Final[str] = (
                "MESSAGES_FILE_PATH must be a path to a file that exists."
            )
            raise ImproperlyConfiguredError(MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE)

        messages_file: IO
        with messages_file_path.open(encoding="utf8") as messages_file:
            e: json.JSONDecodeError
            try:
                return json.load(messages_file)
            except json.JSONDecodeError as e:
                JSON_DECODING_ERROR_MESSAGE: Final[str] = (
                    "Messages JSON file must contain a JSON string that can be decoded "
                    "into a Python dict object."
                )
                raise ImproperlyConfiguredError(JSON_DECODING_ERROR_MESSAGE) from e

    def _setup_welcome_messages(self) -> None:
        messages_dict: Mapping[str, object] = self._get_messages_dict(
            os.getenv("MESSAGES_FILE_PATH")
        )

        if "welcome_messages" not in messages_dict:
            raise MessagesJSONFileMissingKeyError(missing_key="welcome_messages")

        WELCOME_MESSAGES_KEY_IS_VALID: Final[bool] = bool(
            isinstance(messages_dict["welcome_messages"], Iterable)
            and messages_dict["welcome_messages"]
        )
        if not WELCOME_MESSAGES_KEY_IS_VALID:
            raise MessagesJSONFileValueError(
                dict_key="welcome_messages",
                invalid_value=messages_dict["welcome_messages"]
            )

        self._settings["WELCOME_MESSAGES"] = set(messages_dict["welcome_messages"])  # type: ignore[arg-type]

    def _setup_roles_messages(self) -> None:
        messages_dict: Mapping[str, object] = self._get_messages_dict(
            os.getenv("MESSAGES_FILE_PATH")
        )

        if "roles_messages" not in messages_dict:
            raise MessagesJSONFileMissingKeyError(missing_key="roles_messages")

        ROLES_MESSAGES_KEY_IS_VALID: Final[bool] = (
            isinstance(messages_dict["roles_messages"], Iterable)
            and bool(messages_dict["roles_messages"])
        )
        if not ROLES_MESSAGES_KEY_IS_VALID:
            raise MessagesJSONFileValueError(
                dict_key="roles_messages",
                invalid_value=messages_dict["roles_messages"]
            )
        self._settings["ROLES_MESSAGES"] = set(messages_dict["roles_messages"])  # type: ignore[arg-type]

    def _setup_members_page_url(self) -> None:
        raw_members_page_url: str | None = os.getenv("MEMBERS_PAGE_URL")

        MEMBERS_PAGE_URL_IS_VALID: Final[bool] = bool(
            raw_members_page_url
            and validators.url(raw_members_page_url)
        )
        if not MEMBERS_PAGE_URL_IS_VALID:
            INVALID_MEMBERS_PAGE_URL_MESSAGE: Final[str] = (
                "MEMBERS_PAGE_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERS_PAGE_URL_MESSAGE)

        self._settings["MEMBERS_PAGE_URL"] = raw_members_page_url

    def _setup_members_page_cookie(self) -> None:
        raw_members_page_cookie: str | None = os.getenv("MEMBERS_PAGE_COOKIE")

        MEMBERS_PAGE_COOKIE_IS_VALID: Final[bool] = bool(
            raw_members_page_cookie
            and re.match(r"\A[A-Fa-f\d]{128,256}\Z", raw_members_page_cookie)
        )
        if not MEMBERS_PAGE_COOKIE_IS_VALID:
            INVALID_MEMBERS_PAGE_COOKIE_MESSAGE: Final[str] = (
                "MEMBERS_PAGE_COOKIE must be a valid .ASPXAUTH cookie."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERS_PAGE_COOKIE_MESSAGE)

        self._settings["MEMBERS_PAGE_COOKIE"] = raw_members_page_cookie

    def _setup_send_introduction_reminders(self) -> None:
        raw_send_introduction_reminders: str | bool = str(
            os.getenv("SEND_INTRODUCTION_REMINDERS", "Once")
        ).lower()

        if raw_send_introduction_reminders not in VALID_SEND_INTRODUCTION_REMINDERS_VALUES:
            INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE: Final[str] = (
                "SEND_INTRODUCTION_REMINDERS must be one of: "
                "\"Once\", \"Interval\" or \"False\"."
            )
            raise ImproperlyConfiguredError(INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE)

        if raw_send_introduction_reminders in TRUE_VALUES:
            raw_send_introduction_reminders = "once"

        elif raw_send_introduction_reminders not in ("once", "interval"):
            raw_send_introduction_reminders = False

        self._settings["SEND_INTRODUCTION_REMINDERS"] = raw_send_introduction_reminders

    def _setup_introduction_reminder_interval(self) -> None:
        if "SEND_INTRODUCTION_REMINDERS" not in self._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_INTRODUCTION_REMINDERS must be set up "
                "before INTRODUCTION_REMINDER_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_introduction_reminder_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("INTRODUCTION_REMINDER_INTERVAL", "6h"))
        )

        raw_timedelta_details_introduction_reminder_interval: Mapping[str, float] = {
            "hours": 6
        }

        if self._settings["SEND_INTRODUCTION_REMINDERS"]:
            if not raw_introduction_reminder_interval:
                INVALID_INTRODUCTION_REMINDER_INTERVAL_MESSAGE: Final[str] = (
                    "INTRODUCTION_REMINDER_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfiguredError(INVALID_INTRODUCTION_REMINDER_INTERVAL_MESSAGE)

            raw_timedelta_details_introduction_reminder_interval = {
                key: float(value)
                for key, value
                in raw_introduction_reminder_interval.groupdict().items()
                if value
            }

        self._settings["INTRODUCTION_REMINDER_INTERVAL"] = (
            raw_timedelta_details_introduction_reminder_interval
        )

    def _setup_kick_no_introduction_members(self) -> None:
        raw_kick_no_introduction_members: str = str(
            os.getenv("KICK_NO_INTRODUCTION_MEMBERS", "False")
        ).lower()

        if raw_kick_no_introduction_members not in TRUE_VALUES | FALSE_VALUES:
            INVALID_KICK_NO_INTRODUCTION_MEMBERS_MESSAGE: Final[str] = (
                "KICK_NO_INTRODUCTION_MEMBERS must be a boolean value."
            )
            raise ImproperlyConfiguredError(INVALID_KICK_NO_INTRODUCTION_MEMBERS_MESSAGE)

        self._settings["KICK_NO_INTRODUCTION_MEMBERS"] = (
            raw_kick_no_introduction_members in TRUE_VALUES
        )

    def _setup_kick_no_introduction_members_delay(self) -> None:
        if "KICK_NO_INTRODUCTION_MEMBERS" not in self._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: KICK_NO_INTRODUCTION_MEMBERS must be set up "
                "before KICK_NO_INTRODUCTION_MEMBERS_DELAY can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_kick_no_introduction_members_delay: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
            str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS_DELAY", "5d"))
        )

        raw_timedelta_kick_no_introduction_members_delay: timedelta = timedelta()

        if self._settings["KICK_NO_INTRODUCTION_MEMBERS"]:
            if not raw_kick_no_introduction_members_delay:
                INVALID_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE: Final[str] = (
                    "KICK_NO_INTRODUCTION_MEMBERS_DELAY must contain the delay "
                    "in any combination of seconds, minutes, hours, days or weeks."
                )
                raise ImproperlyConfiguredError(
                    INVALID_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE
                )

            raw_timedelta_kick_no_introduction_members_delay = timedelta(
                **{
                    key: float(value)
                    for key, value
                    in raw_kick_no_introduction_members_delay.groupdict().items()
                    if value
                }
            )

            if raw_timedelta_kick_no_introduction_members_delay <= timedelta(days=1):
                TOO_SMALL_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE: Final[str] = (
                    "KICK_NO_INTRODUCTION_MEMBERS_DELAY must be greater than 1 day."
                )
                raise ImproperlyConfiguredError(
                    TOO_SMALL_KICK_NO_INTRODUCTION_MEMBERS_DELAY_MESSAGE
                )

        self._settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = (
            raw_timedelta_kick_no_introduction_members_delay
        )

    def _setup_send_get_roles_reminders(self) -> None:
        raw_send_get_roles_reminders: str = str(
            os.getenv("SEND_GET_ROLES_REMINDERS", "True")
        ).lower()

        if raw_send_get_roles_reminders not in TRUE_VALUES | FALSE_VALUES:
            INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE: Final[str] = (
                "SEND_GET_ROLES_REMINDERS must be a boolean value."
            )
            raise ImproperlyConfiguredError(INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE)

        self._settings["SEND_GET_ROLES_REMINDERS"] = (
            raw_send_get_roles_reminders in TRUE_VALUES
        )

    def _setup_get_roles_reminders_interval(self) -> None:
        if "SEND_GET_ROLES_REMINDERS" not in self._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_GET_ROLES_REMINDERS must be set up "
                "before GET_ROLES_REMINDER_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_get_roles_reminder_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("GET_ROLES_REMINDER_INTERVAL", "24h"))
        )

        raw_timedelta_details_get_roles_reminder_interval: Mapping[str, float] = {"hours": 24}

        if self._settings["SEND_GET_ROLES_REMINDERS"]:
            if not raw_get_roles_reminder_interval:
                INVALID_GET_ROLES_REMINDER_INTERVAL_MESSAGE: Final[str] = (
                    "GET_ROLES_REMINDER_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfiguredError(INVALID_GET_ROLES_REMINDER_INTERVAL_MESSAGE)

            raw_timedelta_details_get_roles_reminder_interval = {
                key: float(value)
                for key, value
                in raw_get_roles_reminder_interval.groupdict().items()
                if value
            }

        self._settings["GET_ROLES_REMINDER_INTERVAL"] = (
            raw_timedelta_details_get_roles_reminder_interval
        )

    def _setup_statistics_days(self) -> None:
        e: ValueError
        try:
            raw_statistics_days: float = float(os.getenv("STATISTICS_DAYS", "30"))
        except ValueError as e:
            INVALID_STATISTICS_DAYS_MESSAGE: Final[str] = (
                "STATISTICS_DAYS must contain the statistics period in days."
            )
            raise ImproperlyConfiguredError(INVALID_STATISTICS_DAYS_MESSAGE) from e

        self._settings["STATISTICS_DAYS"] = timedelta(days=raw_statistics_days)

    def _setup_statistics_roles(self) -> None:
        raw_statistics_roles: str | None = os.getenv("STATISTICS_ROLES")

        if not raw_statistics_roles:
            self._settings["STATISTICS_ROLES"] = DEFAULT_STATISTICS_ROLES

        else:
            self._settings["STATISTICS_ROLES"] = {
                raw_statistics_role
                for raw_statistics_role
                in raw_statistics_roles.split(",")
                if raw_statistics_role
            }

    def _setup_moderation_document_url(self) -> None:
        raw_moderation_document_url: str | None = os.getenv("MODERATION_DOCUMENT_URL")

        MODERATION_DOCUMENT_URL_IS_VALID: Final[bool] = bool(
            raw_moderation_document_url
            and validators.url(raw_moderation_document_url)
        )
        if not MODERATION_DOCUMENT_URL_IS_VALID:
            MODERATION_DOCUMENT_URL_MESSAGE: Final[str] = (
                "MODERATION_DOCUMENT_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(MODERATION_DOCUMENT_URL_MESSAGE)

        self._settings["MODERATION_DOCUMENT_URL"] = raw_moderation_document_url

    def _setup_manual_moderation_warning_message_location(self) -> None:
        raw_manual_moderation_warning_message_location: str = os.getenv(
            "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION",
            "DM"
        )
        if not self._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"]:
            MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE: Final[str] = (
                "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION must be a valid name "
                "of a channel in the CSS Discord server."
            )
            raise ImproperlyConfiguredError(MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE)

        self._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = (
            raw_manual_moderation_warning_message_location
        )

    def _setup_env_variables(self) -> None:  # noqa: C901, PLR0912
        """
        Load environment values into the settings dictionary.

        Environment values are loaded from the .env file/the current environment variables and
        are only stored after the input values have been validated.
        """
        if self._is_env_variables_setup:
            logging.warning("Environment variables have already been set up.")
            return

        dotenv.load_dotenv()

        self._setup_logging()
        self._setup_discord_bot_token()
        self._setup_discord_log_channel_webhook_url()
        self._setup_guild_id()
        self._setup_ping_command_easter_egg_probability()
        self._setup_welcome_messages()
        self._setup_roles_messages()
        self._setup_members_page_url()
        self._setup_members_page_cookie()
        self._setup_send_introduction_reminders()
        self._setup_introduction_reminder_interval()
        self._setup_kick_no_introduction_members()
        self._setup_kick_no_introduction_members_delay()
        self._setup_send_get_roles_reminders()
        self._setup_get_roles_reminders_interval()
        self._setup_statistics_days()
        self._setup_statistics_roles()
        self._setup_moderation_document_url()

        self._is_env_variables_setup = True


settings: Final[Settings] = Settings()


def run_setup() -> None:
    """Execute the setup functions required, before other modules can be run."""
    # noinspection PyProtectedMember
    settings._setup_env_variables()  # noqa: SLF001

    logging.debug("Begin database setup")
    management.call_command("migrate")
    logging.debug("Database setup completed")
