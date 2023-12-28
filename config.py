"""
Contains settings values and import & setup functions.

Settings values are imported from the .env file or the current environment variables.
These values are used to configure the functionality of the bot at run-time.
"""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "TRUE_VALUES",
    "FALSE_VALUES",
    "VALID_SEND_INTRODUCTION_REMINDERS_VALUES",
    "DEFAULT_STATISTICS_ROLES",
    "LOG_LEVEL_CHOICES",
    "settings",
    "setup_env_variables",
    "setup_django"
)

import abc
import functools
import json
import logging
import os
import re
from collections.abc import Iterable, Mapping
from datetime import timedelta
from logging import Logger
from pathlib import Path
from re import Match
from typing import IO, Any, ClassVar, Final, final

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


logger: Logger = logging.getLogger("texbot")


class Settings(abc.ABC):
    """
    Settings class that provides access to all settings values.

    Settings values can be accessed via key (like a dictionary) or via class attribute.
    """

    _is_env_variables_setup: ClassVar[bool]
    _settings: ClassVar[dict[str, object]]

    @classmethod
    def get_invalid_settings_key_message(cls, item: str) -> str:
        """Return the message to state that the given settings key is invalid."""
        return f"{item!r} is not a valid settings key."

    def __getattr__(self, item: str) -> Any:
        """Retrieve settings value by attribute lookup."""
        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

        if "_pytest" in item or item in ("__bases__", "__test__"):  # HACK: Overriding __getattr__() leads to many edge-case issues where external libraries will attempt to call getattr() with peculiar values # noqa: FIX004
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if not self._is_env_variables_setup:
            self._setup_env_variables()

        if item in self._settings:
            return self._settings[item]

        if re.match(r"\A[A-Z](?:[A-Z_]*[A-Z])?\Z", item):
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = self.get_invalid_settings_key_message(
                item
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

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

        logger.setLevel(getattr(logging, raw_console_log_level))

        console_logging_handler: logging.Handler = logging.StreamHandler()
        # noinspection SpellCheckingInspection
        console_logging_handler.setFormatter(
            logging.Formatter("{asctime} - {name} - {levelname}", style="{")
        )

        logger.addHandler(console_logging_handler)

    @classmethod
    def _setup_discord_bot_token(cls) -> None:
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

        cls._settings["DISCORD_BOT_TOKEN"] = raw_discord_bot_token

    @classmethod
    def _setup_discord_log_channel_webhook_url(cls) -> None:
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

        cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = raw_discord_log_channel_webhook_url

    @classmethod
    def _setup_discord_guild_id(cls) -> None:
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

        cls._settings["DISCORD_GUILD_ID"] = int(raw_discord_guild_id)  # type: ignore[arg-type]

    @classmethod
    def _setup_group_name(cls) -> None:
        raw_group_name: str | None = os.getenv("GROUP_NAME")

        GROUP_NAME_IS_VALID: Final[bool] = bool(
            not raw_group_name
            or re.match(r"\A[A-Za-z0-9 '&!?:,.#%\"-]+\Z", group_name)
        )
        if not GROUP_NAME_IS_VALID:
            INVALID_GROUP_NAME_MESSAGE: Final[str] = ("GROUP_NAME must not contain any invalid characters.")
            raise ImproperlyConfiguredError(INVALID_GROUP_NAME_MESSAGE)

        cls._settings["_GROUP_NAME"] = raw_group_name

    @classmethod
    def _setup_purchase_membership_url(cls) -> None:
        raw_purchase_membership_url: str | None = os.getenv("PURCHASE_MEMBERSHIP_URL")

        PURCHASE_MEMBERSHIP_URL_IS_VALID: Final[bool] = bool(
            not raw_purchase_membership_url
            or validators.url(raw_purchase_membership_url)
        )
        if not PURCHASE_MEMBERSHIP_URL_IS_VALID:
            INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE: Final[str] = (
                "PURCHASE_MEMBERSHIP_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE)

        cls._settings["PURCHASE_MEMBERSHIP_URL"] = raw_purchase_membership_url

    @classmethod
    def _setup_membership_perks_url(cls) -> None:
        raw_membership_perks_url: str | None = os.getenv("MEMBERSHIP_PERKS_URL")

        MEMBERSHIP_PERKS_URL_IS_VALID: Final[bool] = bool(
            not raw_membership_perks_url
            or validators.url(raw_membership_perks_url)
        )
        if not MEMBERSHIP_PERKS_URL_IS_VALID:
            INVALID_MEMBERSHIP_PERKS_URL_MESSAGE: Final[str] = (
                "MEMBERSHIP_PERKS_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERSHIP_PERKS_URL_MESSAGE)

        cls._settings["MEMBERSHIP_PERKS_URL"] = raw_membership_perks_url

    @classmethod
    def _setup_ping_command_easter_egg_probability(cls) -> None:
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

        cls._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
            raw_ping_command_easter_egg_probability
        )

    @staticmethod
    @functools.lru_cache(maxsize=5)
    def _get_messages_dict(raw_messages_file_path: str | None) -> Mapping[str, object]:
        JSON_DECODING_ERROR_MESSAGE: Final[str] = (
            "Messages JSON file must contain a JSON string that can be decoded "
            "into a Python dict object."
        )

        messages_file_path: Path = (
            Path(raw_messages_file_path) if raw_messages_file_path else Path("messages.json")
        )

        if not messages_file_path.is_file():
            MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE: Final[str] = (
                "MESSAGES_FILE_PATH must be a path to a file that exists."
            )
            raise ImproperlyConfiguredError(MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE)

        messages_file: IO[str]
        with messages_file_path.open(encoding="utf8") as messages_file:
            e: json.JSONDecodeError
            try:
                messages_dict: object = json.load(messages_file)
            except json.JSONDecodeError as e:
                raise ImproperlyConfiguredError(JSON_DECODING_ERROR_MESSAGE) from e

        if not isinstance(messages_dict, Mapping):
            raise ImproperlyConfiguredError(JSON_DECODING_ERROR_MESSAGE)

        return messages_dict

    @classmethod
    def _setup_welcome_messages(cls) -> None:
        messages_dict: Mapping[str, object] = cls._get_messages_dict(
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

        cls._settings["WELCOME_MESSAGES"] = set(messages_dict["welcome_messages"])  # type: ignore[call-overload]

    @classmethod
    def _setup_roles_messages(cls) -> None:
        messages_dict: Mapping[str, object] = cls._get_messages_dict(
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
        cls._settings["ROLES_MESSAGES"] = set(messages_dict["roles_messages"])  # type: ignore[call-overload]

    @classmethod
    def _setup_members_list_url(cls) -> None:
        raw_members_list_url: str | None = os.getenv("MEMBERS_LIST_URL")

        MEMBERS_LIST_URL_IS_VALID: Final[bool] = bool(
            raw_members_list_url
            and validators.url(raw_members_list_url)
        )
        if not MEMBERS_LIST_URL_IS_VALID:
            INVALID_MEMBERS_LIST_URL_MESSAGE: Final[str] = (
                "MEMBERS_LIST_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERS_LIST_URL_MESSAGE)

        cls._settings["MEMBERS_LIST_URL"] = raw_members_list_url

    @classmethod
    def _setup_members_list_url_session_cookie(cls) -> None:
        raw_members_list_url_session_cookie: str | None = os.getenv(
            "MEMBERS_LIST_URL_SESSION_COOKIE"
        )

        MEMBERS_LIST_URL_SESSION_COOKIE_IS_VALID: Final[bool] = bool(
            raw_members_list_url_session_cookie
            and re.match(r"\A[A-Fa-f\d]{128,256}\Z", raw_members_list_url_session_cookie)
        )
        if not MEMBERS_LIST_URL_SESSION_COOKIE_IS_VALID:
            INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE: Final[str] = (
                "MEMBERS_LIST_URL_SESSION_COOKIE must be a valid .ASPXAUTH cookie."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE)

        cls._settings["MEMBERS_LIST_URL_SESSION_COOKIE"] = raw_members_list_url_session_cookie

    @classmethod
    def _setup_send_introduction_reminders(cls) -> None:
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

        cls._settings["SEND_INTRODUCTION_REMINDERS"] = raw_send_introduction_reminders

    @classmethod
    def _setup_send_introduction_reminders_interval(cls) -> None:
        if "SEND_INTRODUCTION_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_INTRODUCTION_REMINDERS must be set up "
                "before SEND_INTRODUCTION_REMINDERS_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_send_introduction_reminders_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("SEND_INTRODUCTION_REMINDERS_INTERVAL", "6h"))
        )

        raw_timedelta_details_send_introduction_reminders_interval: Mapping[str, float] = {
            "hours": 6
        }

        if cls._settings["SEND_INTRODUCTION_REMINDERS"]:
            if not raw_send_introduction_reminders_interval:
                INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
                    "SEND_INTRODUCTION_REMINDERS_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfiguredError(
                    INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE
                )

            raw_timedelta_details_send_introduction_reminders_interval = {
                key: float(value)
                for key, value
                in raw_send_introduction_reminders_interval.groupdict().items()
                if value
            }

        cls._settings["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
            raw_timedelta_details_send_introduction_reminders_interval
        )

    @classmethod
    def _setup_kick_no_introduction_discord_members(cls) -> None:
        raw_kick_no_introduction_discord_members: str = str(
            os.getenv("KICK_NO_INTRODUCTION_DISCORD_MEMBERS", "False")
        ).lower()

        if raw_kick_no_introduction_discord_members not in TRUE_VALUES | FALSE_VALUES:
            INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_MESSAGE: Final[str] = (
                "KICK_NO_INTRODUCTION_DISCORD_MEMBERS must be a boolean value."
            )
            raise ImproperlyConfiguredError(
                INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_MESSAGE
            )

        cls._settings["KICK_NO_INTRODUCTION_MEMBERS"] = (
            raw_kick_no_introduction_discord_members in TRUE_VALUES
        )

    @classmethod
    def _setup_kick_no_introduction_discord_members_delay(cls) -> None:
        if "KICK_NO_INTRODUCTION_DISCORD_MEMBERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: KICK_NO_INTRODUCTION_DISCORD_MEMBERS must be set up "
                "before KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_kick_no_introduction_discord_members_delay: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
            str(os.getenv("KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY", "5d"))
        )

        raw_timedelta_kick_no_introduction_discord_members_delay: timedelta = timedelta()

        if cls._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS"]:
            if not raw_kick_no_introduction_discord_members_delay:
                INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE: Final[str] = (
                    "KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY must contain the delay "
                    "in any combination of seconds, minutes, hours, days or weeks."
                )
                raise ImproperlyConfiguredError(
                    INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE
                )

            raw_timedelta_kick_no_introduction_discord_members_delay = timedelta(
                **{
                    key: float(value)
                    for key, value
                    in raw_kick_no_introduction_discord_members_delay.groupdict().items()
                    if value
                }
            )

            if raw_timedelta_kick_no_introduction_discord_members_delay <= timedelta(days=1):
                TOO_SMALL_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE: Final[str] = (
                    "KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY must be greater than 1 day."
                )
                raise ImproperlyConfiguredError(
                    TOO_SMALL_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE
                )

        cls._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY"] = (
            RAW_TIMEDELTA_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY
        )

    @classmethod
    def _setup_send_get_roles_reminders(cls) -> None:
        raw_send_get_roles_reminders: str = str(
            os.getenv("SEND_GET_ROLES_REMINDERS", "True")
        ).lower()

        if raw_send_get_roles_reminders not in TRUE_VALUES | FALSE_VALUES:
            INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE: Final[str] = (
                "SEND_GET_ROLES_REMINDERS must be a boolean value."
            )
            raise ImproperlyConfiguredError(INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE)

        cls._settings["SEND_GET_ROLES_REMINDERS"] = (
            raw_send_get_roles_reminders in TRUE_VALUES
        )

    @classmethod
    def _setup_send_get_roles_reminders_interval(cls) -> None:
        if "SEND_GET_ROLES_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_GET_ROLES_REMINDERS must be set up "
                "before SEND_GET_ROLES_REMINDERS_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_send_get_roles_reminders_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("SEND_GET_ROLES_REMINDERS_INTERVAL", "24h"))
        )

        raw_timedelta_details_send_get_roles_reminders_interval: Mapping[str, float] = {
            "hours": 24
        }

        if cls._settings["SEND_GET_ROLES_REMINDERS"]:
            if not raw_send_get_roles_reminders_interval:
                INVALID_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
                    "SEND_GET_ROLES_REMINDERS_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfiguredError(
                    INVALID_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE
                )

            raw_timedelta_details_send_get_roles_reminders_interval = {
                key: float(value)
                for key, value
                in raw_send_get_roles_reminders_interval.groupdict().items()
                if value
            }

        cls._settings["SEND_GET_ROLES_REMINDERS_INTERVAL"] = (
            raw_timedelta_details_send_get_roles_reminders_interval
        )

    @classmethod
    def _setup_statistics_days(cls) -> None:
        e: ValueError
        try:
            raw_statistics_days: float = float(os.getenv("STATISTICS_DAYS", "30"))
        except ValueError as e:
            INVALID_STATISTICS_DAYS_MESSAGE: Final[str] = (
                "STATISTICS_DAYS must contain the statistics period in days."
            )
            raise ImproperlyConfiguredError(INVALID_STATISTICS_DAYS_MESSAGE) from e

        cls._settings["STATISTICS_DAYS"] = timedelta(days=raw_statistics_days)

    @classmethod
    def _setup_statistics_roles(cls) -> None:
        raw_statistics_roles: str | None = os.getenv("STATISTICS_ROLES")

        if not raw_statistics_roles:
            cls._settings["STATISTICS_ROLES"] = DEFAULT_STATISTICS_ROLES

        else:
            cls._settings["STATISTICS_ROLES"] = {
                raw_statistics_role
                for raw_statistics_role
                in raw_statistics_roles.split(",")
                if raw_statistics_role
            }

    @classmethod
    def _setup_moderation_document_url(cls) -> None:
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

        cls._settings["MODERATION_DOCUMENT_URL"] = raw_moderation_document_url

    @classmethod
    def _setup_manual_moderation_warning_message_location(cls) -> None:
        raw_manual_moderation_warning_message_location: str = os.getenv(
            "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION",
            "DM"
        )
        if not cls._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"]:
            MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE: Final[str] = (
                "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION must be a valid name "
                "of a channel in your group's Discord guild."
            )
            raise ImproperlyConfiguredError(MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE)

        cls._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = (
            raw_manual_moderation_warning_message_location
        )

    @classmethod
    def _setup_env_variables(cls) -> None:
        """
        Load environment values into the settings dictionary.

        Environment values are loaded from the .env file/the current environment variables and
        are only stored after the input values have been validated.
        """
        if cls._is_env_variables_setup:
            logger.warning("Environment variables have already been set up.")
            return

        dotenv.load_dotenv()

        cls._setup_logging()
        cls._setup_discord_bot_token()
        cls._setup_discord_log_channel_webhook_url()
        cls._setup_guild_id()
        cls._setup_ping_command_easter_egg_probability()
        cls._setup_welcome_messages()
        cls._setup_roles_messages()
        cls._setup_members_page_url()
        cls._setup_members_page_cookie()
        cls._setup_send_introduction_reminders()
        cls._setup_introduction_reminder_interval()
        cls._setup_kick_no_introduction_members()
        cls._setup_kick_no_introduction_members_delay()
        cls._setup_send_get_roles_reminders()
        cls._setup_get_roles_reminders_interval()
        cls._setup_statistics_days()
        cls._setup_statistics_roles()
        cls._setup_moderation_document_url()
        cls._setup_manual_moderation_warning_message_location()

        cls._is_env_variables_setup = True


def _settings_class_factory() -> type[Settings]:
    @final
    class RuntimeSettings(Settings):
        """
        Settings class that provides access to all settings values.

        Settings values can be accessed via key (like a dictionary) or via class attribute.
        """

        _is_env_variables_setup: ClassVar[bool] = False
        _settings: ClassVar[dict[str, object]] = {}

    return RuntimeSettings


settings: Final[Settings] = _settings_class_factory()()


def run_setup() -> None:
    """Execute the setup functions required, before other modules can be run."""
    # noinspection PyProtectedMember
    settings._setup_env_variables()  # noqa: SLF001

    logger.debug("Begin database setup")
    management.call_command("migrate")
    logger.debug("Database setup completed")
