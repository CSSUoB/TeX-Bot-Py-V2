"""
Contains settings values and import and setup functions.

Settings values are imported from the .env file or the current environment variables.
These values are used to configure the functionality of the bot at run-time.
"""

import abc
import functools
import importlib
import json
import logging
import os
import re
from collections.abc import Iterable, Mapping
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, final

import dotenv
import validators
from discord_logging.handler import DiscordHandler

from exceptions import (
    ImproperlyConfiguredError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import IO, Any, ClassVar, Final

__all__: "Sequence[str]" = (
    "DEFAULT_STATISTICS_ROLES",
    "FALSE_VALUES",
    "LOG_LEVEL_CHOICES",
    "TRUE_VALUES",
    "VALID_SEND_INTRODUCTION_REMINDERS_VALUES",
    "run_setup",
    "settings",
)

PROJECT_ROOT: "Final[Path]" = Path(__file__).parent.resolve()

TRUE_VALUES: "Final[frozenset[str]]" = frozenset({"true", "1", "t", "y", "yes", "on"})
FALSE_VALUES: "Final[frozenset[str]]" = frozenset({"false", "0", "f", "n", "no", "off"})
VALID_SEND_INTRODUCTION_REMINDERS_VALUES: "Final[frozenset[str]]" = frozenset(
    {"once"} | TRUE_VALUES | FALSE_VALUES,
)
DEFAULT_STATISTICS_ROLES: "Final[frozenset[str]]" = frozenset(
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
        "Quiz Victor",
    },
)
LOG_LEVEL_CHOICES: "Final[Sequence[str]]" = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class Settings(abc.ABC):
    """
    Settings class that provides access to all settings values.

    Settings values can be accessed via key (like a dictionary) or via class attribute.
    """

    _is_env_variables_setup: "ClassVar[bool]"
    _settings: "ClassVar[dict[str, object]]"

    @classmethod
    def get_invalid_settings_key_message(cls, item: str) -> str:
        """Return the message to state that the given settings key is invalid."""
        return f"{item!r} is not a valid settings key."

    def __getattr__(self, item: str) -> "Any":  # type: ignore[explicit-any]  # noqa: ANN401
        """Retrieve settings value by attribute lookup."""
        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

        if (
            "_pytest" in item or item in ("__bases__", "__test__")
        ):  # NOTE: Overriding __getattr__() leads to many edge-case issues where external libraries will attempt to call getattr() with peculiar values
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if not self._is_env_variables_setup:
            self._setup_env_variables()

        if item in self._settings:
            return self._settings[item]

        if re.fullmatch(r"\A[A-Z](?:[A-Z_]*[A-Z])?\Z", item):
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = self.get_invalid_settings_key_message(
                item,
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

    def __getitem__(self, item: str) -> "Any":  # type: ignore[explicit-any]  # noqa: ANN401
        """Retrieve settings value by key lookup."""
        attribute_not_exist_error: AttributeError
        try:
            return getattr(self, item)
        except AttributeError as attribute_not_exist_error:
            key_error_message: str = item

            if self.get_invalid_settings_key_message(item) in str(attribute_not_exist_error):
                key_error_message = str(attribute_not_exist_error)

            raise KeyError(key_error_message) from None

    @staticmethod
    def _setup_logging() -> None:
        raw_console_log_level: str = str(os.getenv("CONSOLE_LOG_LEVEL", "INFO")).upper()

        if raw_console_log_level not in LOG_LEVEL_CHOICES:
            INVALID_LOG_LEVEL_MESSAGE: Final[str] = f"""LOG_LEVEL must be one of {
                ",".join(
                    f"{log_level_choice!r}" for log_level_choice in LOG_LEVEL_CHOICES[:-1]
                )
            } or {LOG_LEVEL_CHOICES[-1]!r}."""
            raise ImproperlyConfiguredError(INVALID_LOG_LEVEL_MESSAGE)

        logger.setLevel(getattr(logging, raw_console_log_level))

        console_logging_handler: logging.Handler = logging.StreamHandler()
        console_logging_handler.setFormatter(
            logging.Formatter("{asctime} | {name} | {levelname:^8} - {message}", style="{"),
        )

        logger.addHandler(console_logging_handler)
        logger.propagate = False

    @classmethod
    def _setup_discord_bot_token(cls) -> None:
        raw_discord_bot_token: str | None = os.getenv("DISCORD_BOT_TOKEN")

        DISCORD_BOT_TOKEN_IS_VALID: Final[bool] = bool(
            raw_discord_bot_token
            and re.fullmatch(
                r"\A([A-Za-z0-9_-]{24,26})\.([A-Za-z0-9_-]{6})\.([A-Za-z0-9_-]{27,38})\Z",
                raw_discord_bot_token,
            ),
        )
        if not DISCORD_BOT_TOKEN_IS_VALID:
            INVALID_DISCORD_BOT_TOKEN_MESSAGE: Final[str] = (
                "DISCORD_BOT_TOKEN must be a valid Discord bot token "  # noqa: S105
                "(see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_BOT_TOKEN_MESSAGE)

        cls._settings["DISCORD_BOT_TOKEN"] = raw_discord_bot_token

    @classmethod
    def _setup_discord_log_channel_webhook(cls) -> "Logger":
        raw_discord_log_channel_webhook_url: str = os.getenv(
            "DISCORD_LOG_CHANNEL_WEBHOOK_URL", ""
        )

        if raw_discord_log_channel_webhook_url and (
            not validators.url(raw_discord_log_channel_webhook_url)
            or not raw_discord_log_channel_webhook_url.startswith(
                "https://discord.com/api/webhooks/"
            )
        ):
            INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE: Final[str] = (
                "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL "
                "that points to a discord channel where logs should be displayed."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE)

        webhook_config_logger: Logger = logging.getLogger("_temp_webhook_config")

        if raw_discord_log_channel_webhook_url:
            discord_logging_handler: logging.Handler = DiscordHandler(
                service_name="TeX-Bot", webhook_url=raw_discord_log_channel_webhook_url
            )

            discord_logging_handler.setLevel(logging.WARNING)

            discord_logging_handler.setFormatter(
                logging.Formatter("{levelname} | {message}", style="{")
            )

            webhook_config_logger.addHandler(discord_logging_handler)

        cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = raw_discord_log_channel_webhook_url

        return webhook_config_logger

    @classmethod
    def _setup_discord_guild_id(cls) -> None:
        raw_discord_guild_id: str | None = os.getenv("DISCORD_GUILD_ID")

        DISCORD_GUILD_ID_IS_VALID: Final[bool] = bool(
            raw_discord_guild_id and re.fullmatch(r"\A\d{17,20}\Z", raw_discord_guild_id),
        )
        if not DISCORD_GUILD_ID_IS_VALID:
            INVALID_DISCORD_GUILD_ID_MESSAGE: Final[str] = (
                "DISCORD_GUILD_ID must be a valid Discord guild ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_GUILD_ID_MESSAGE)

        cls._settings["_DISCORD_MAIN_GUILD_ID"] = int(raw_discord_guild_id)  # type: ignore[arg-type]

    @classmethod
    def _setup_group_full_name(cls) -> None:
        raw_group_full_name: str | None = os.getenv("GROUP_NAME")

        GROUP_FULL_NAME_IS_VALID: Final[bool] = bool(
            not raw_group_full_name
            or re.fullmatch(r"\A[A-Za-z0-9 '&!?:,.#%\"-]+\Z", raw_group_full_name),
        )
        if not GROUP_FULL_NAME_IS_VALID:
            INVALID_GROUP_FULL_NAME: Final[str] = (
                "GROUP_NAME must not contain any invalid characters."
            )
            raise ImproperlyConfiguredError(INVALID_GROUP_FULL_NAME)

        cls._settings["_GROUP_FULL_NAME"] = raw_group_full_name

    @classmethod
    def _setup_group_short_name(cls) -> None:
        raw_group_short_name: str | None = os.getenv("GROUP_SHORT_NAME")

        GROUP_SHORT_NAME_IS_VALID: Final[bool] = bool(
            not raw_group_short_name
            or re.fullmatch(r"\A[A-Za-z0-9'&!?:,.#%\"-]+\Z", raw_group_short_name),
        )
        if not GROUP_SHORT_NAME_IS_VALID:
            INVALID_GROUP_SHORT_NAME: Final[str] = (
                "GROUP_SHORT_NAME must not contain any invalid characters."
            )
            raise ImproperlyConfiguredError(INVALID_GROUP_SHORT_NAME)

        cls._settings["_GROUP_SHORT_NAME"] = raw_group_short_name

    @classmethod
    def _setup_purchase_membership_url(cls) -> None:
        raw_purchase_membership_url: str | None = os.getenv("PURCHASE_MEMBERSHIP_URL")

        PURCHASE_MEMBERSHIP_URL_IS_VALID: Final[bool] = bool(
            not raw_purchase_membership_url or validators.url(raw_purchase_membership_url),
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
            not raw_membership_perks_url or validators.url(raw_membership_perks_url),
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
                os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01"),
            )
        except ValueError as e:
            raise (
                ImproperlyConfiguredError(INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE)
            ) from e

        if not 0 <= raw_ping_command_easter_egg_probability <= 100:
            raise ImproperlyConfiguredError(
                INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE,
            )

        cls._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
            raw_ping_command_easter_egg_probability
        )

    @classmethod
    @functools.lru_cache(maxsize=5)
    def _get_messages_dict(cls, raw_messages_file_path: str | None) -> Mapping[str, object]:
        JSON_DECODING_ERROR_MESSAGE: Final[str] = (
            "Messages JSON file must contain a JSON string that can be decoded "
            "into a Python dict object."
        )

        messages_file_path: Path = (
            Path(raw_messages_file_path)
            if raw_messages_file_path
            else PROJECT_ROOT / Path("messages.json")
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
            os.getenv("MESSAGES_FILE_PATH"),
        )

        if "welcome_messages" not in messages_dict:
            raise MessagesJSONFileMissingKeyError(missing_key="welcome_messages")

        WELCOME_MESSAGES_KEY_IS_VALID: Final[bool] = bool(
            isinstance(messages_dict["welcome_messages"], Iterable)
            and messages_dict["welcome_messages"],
        )
        if not WELCOME_MESSAGES_KEY_IS_VALID:
            raise MessagesJSONFileValueError(
                dict_key="welcome_messages",
                invalid_value=messages_dict["welcome_messages"],
            )

        cls._settings["WELCOME_MESSAGES"] = set(messages_dict["welcome_messages"])  # type: ignore[call-overload]

    @classmethod
    def _setup_roles_messages(cls) -> None:
        messages_dict: Mapping[str, object] = cls._get_messages_dict(
            os.getenv("MESSAGES_FILE_PATH"),
        )

        if "roles_messages" not in messages_dict:
            raise MessagesJSONFileMissingKeyError(missing_key="roles_messages")

        ROLES_MESSAGES_KEY_IS_VALID: Final[bool] = isinstance(
            messages_dict["roles_messages"], Iterable
        ) and bool(messages_dict["roles_messages"])
        if not ROLES_MESSAGES_KEY_IS_VALID:
            raise MessagesJSONFileValueError(
                dict_key="roles_messages",
                invalid_value=messages_dict["roles_messages"],
            )

        cls._settings["ROLES_MESSAGES"] = set(messages_dict["roles_messages"])  # type: ignore[call-overload]

    @classmethod
    def _setup_organisation_id(cls) -> None:
        raw_organisation_id: str | None = os.getenv("ORGANISATION_ID")

        ORGANISATION_ID_IS_VALID: Final[bool] = bool(
            raw_organisation_id and re.fullmatch(r"\A\d{4,5}\Z", raw_organisation_id),
        )

        if not ORGANISATION_ID_IS_VALID:
            INVALID_ORGANISATION_ID_MESSAGE: Final[str] = (
                "ORGANISATION_ID must be an integer 4 to 5 digits long."
            )
            raise ImproperlyConfiguredError(message=INVALID_ORGANISATION_ID_MESSAGE)

        cls._settings["ORGANISATION_ID"] = raw_organisation_id

    @classmethod
    def _setup_members_list_auth_session_cookie(cls) -> None:
        raw_members_list_auth_session_cookie: str | None = os.getenv(
            "MEMBERS_LIST_URL_SESSION_COOKIE",
        )

        MEMBERS_LIST_AUTH_SESSION_COOKIE_IS_VALID: Final[bool] = bool(
            raw_members_list_auth_session_cookie
            and re.fullmatch(r"\A[A-Fa-f\d]{128,256}\Z", raw_members_list_auth_session_cookie),
        )
        if not MEMBERS_LIST_AUTH_SESSION_COOKIE_IS_VALID:
            INVALID_MEMBERS_LIST_AUTH_SESSION_COOKIE_MESSAGE: Final[str] = (
                "MEMBERS_LIST_URL_SESSION_COOKIE must be a valid .ASPXAUTH cookie."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERS_LIST_AUTH_SESSION_COOKIE_MESSAGE)

        cls._settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"] = (
            raw_members_list_auth_session_cookie
        )

    @classmethod
    def _setup_send_introduction_reminders(cls) -> None:
        raw_send_introduction_reminders: str | bool = str(
            os.getenv("SEND_INTRODUCTION_REMINDERS", "Once"),
        ).lower()

        if raw_send_introduction_reminders not in VALID_SEND_INTRODUCTION_REMINDERS_VALUES:
            INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE: Final[str] = (
                'SEND_INTRODUCTION_REMINDERS must be one of: "Once", "Interval" or "False".'
            )
            raise ImproperlyConfiguredError(INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE)

        if raw_send_introduction_reminders in TRUE_VALUES:
            raw_send_introduction_reminders = "once"

        elif raw_send_introduction_reminders not in ("once", "interval"):
            raw_send_introduction_reminders = False

        cls._settings["SEND_INTRODUCTION_REMINDERS"] = raw_send_introduction_reminders

    @classmethod
    def _setup_send_introduction_reminders_delay(cls) -> None:
        if "SEND_INTRODUCTION_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_INTRODUCTION_REMINDERS must be set up "
                "before SEND_INTRODUCTION_REMINDERS_DELAY can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_send_introduction_reminders_delay: re.Match[str] | None = re.fullmatch(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
            str(os.getenv("SEND_INTRODUCTION_REMINDERS_DELAY", "40h")),
        )

        raw_timedelta_send_introduction_reminders_delay: timedelta = timedelta()

        if cls._settings["SEND_INTRODUCTION_REMINDERS"]:
            if not raw_send_introduction_reminders_delay:
                INVALID_SEND_INTRODUCTION_REMINDERS_DELAY_MESSAGE: Final[str] = (
                    "SEND_INTRODUCTION_REMINDERS_DELAY must contain the delay "
                    "in any combination of seconds, minutes, hours, days or weeks."
                )
                raise ImproperlyConfiguredError(
                    INVALID_SEND_INTRODUCTION_REMINDERS_DELAY_MESSAGE,
                )

            raw_timedelta_send_introduction_reminders_delay = timedelta(
                **{
                    key: float(value)
                    for key, value in raw_send_introduction_reminders_delay.groupdict().items()
                    if value
                },
            )

            if raw_timedelta_send_introduction_reminders_delay < timedelta(days=1):
                TOO_SMALL_SEND_INTRODUCTION_REMINDERS_DELAY_MESSAGE: Final[str] = (
                    "SEND_INTRODUCTION_REMINDERS_DELAY must be longer than or equal to 1 day "
                    "(in any allowed format)."
                )
                raise ImproperlyConfiguredError(
                    TOO_SMALL_SEND_INTRODUCTION_REMINDERS_DELAY_MESSAGE,
                )

        cls._settings["SEND_INTRODUCTION_REMINDERS_DELAY"] = (
            raw_timedelta_send_introduction_reminders_delay
        )

    @classmethod
    def _setup_send_introduction_reminders_interval(cls) -> None:
        if "SEND_INTRODUCTION_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_INTRODUCTION_REMINDERS must be set up "
                "before SEND_INTRODUCTION_REMINDERS_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_send_introduction_reminders_interval: re.Match[str] | None = re.fullmatch(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("SEND_INTRODUCTION_REMINDERS_INTERVAL", "6h")),
        )

        raw_timedelta_details_send_introduction_reminders_interval: Mapping[str, float] = {
            "hours": 6,
        }

        if cls._settings["SEND_INTRODUCTION_REMINDERS"]:
            if not raw_send_introduction_reminders_interval:
                INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
                    "SEND_INTRODUCTION_REMINDERS_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfiguredError(
                    INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE,
                )

            raw_timedelta_details_send_introduction_reminders_interval = {
                key: float(value)
                for key, value in raw_send_introduction_reminders_interval.groupdict().items()
                if value
            }

        cls._settings["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
            raw_timedelta_details_send_introduction_reminders_interval
        )

    @classmethod
    def _setup_send_get_roles_reminders(cls) -> None:
        raw_send_get_roles_reminders: str = str(
            os.getenv("SEND_GET_ROLES_REMINDERS", "True"),
        ).lower()

        if raw_send_get_roles_reminders not in TRUE_VALUES | FALSE_VALUES:
            INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE: Final[str] = (
                "SEND_GET_ROLES_REMINDERS must be a boolean value."
            )
            raise ImproperlyConfiguredError(INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE)

        cls._settings["SEND_GET_ROLES_REMINDERS"] = raw_send_get_roles_reminders in TRUE_VALUES

    @classmethod
    def _setup_send_get_roles_reminders_delay(cls) -> None:
        if "SEND_GET_ROLES_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_GET_ROLES_REMINDERS must be set up "
                "before SEND_GET_ROLES_REMINDERS_DELAY can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_send_get_roles_reminders_delay: re.Match[str] | None = re.fullmatch(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
            str(os.getenv("SEND_GET_ROLES_REMINDERS_DELAY", "40h")),
        )

        raw_timedelta_send_get_roles_reminders_delay: timedelta = timedelta()

        if cls._settings["SEND_GET_ROLES_REMINDERS"]:
            if not raw_send_get_roles_reminders_delay:
                INVALID_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE: Final[str] = (
                    "SEND_GET_ROLES_REMINDERS_DELAY must contain the delay "
                    "in any combination of seconds, minutes, hours, days or weeks."
                )
                raise ImproperlyConfiguredError(
                    INVALID_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE,
                )

            raw_timedelta_send_get_roles_reminders_delay = timedelta(
                **{
                    key: float(value)
                    for key, value in raw_send_get_roles_reminders_delay.groupdict().items()
                    if value
                },
            )

            if raw_timedelta_send_get_roles_reminders_delay < timedelta(days=1):
                TOO_SMALL_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE: Final[str] = (
                    "SEND_SEND_GET_ROLES_REMINDERS_DELAY "
                    "must be longer than or equal to 1 day (in any allowed format)."
                )
                raise ImproperlyConfiguredError(
                    TOO_SMALL_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE,
                )

        cls._settings["SEND_GET_ROLES_REMINDERS_DELAY"] = (
            raw_timedelta_send_get_roles_reminders_delay
        )

    @classmethod
    def _setup_advanced_send_get_roles_reminders_interval(cls) -> None:
        if "SEND_GET_ROLES_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_GET_ROLES_REMINDERS must be set up "
                "before ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_advanced_send_get_roles_reminders_interval: re.Match[str] | None = re.fullmatch(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL", "24h")),
        )

        raw_timedelta_details_advanced_send_get_roles_reminders_interval: Mapping[
            str, float
        ] = {
            "hours": 24,
        }

        if cls._settings["SEND_GET_ROLES_REMINDERS"]:
            if not raw_advanced_send_get_roles_reminders_interval:
                INVALID_ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
                    "ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfiguredError(
                    INVALID_ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE,
                )

            raw_timedelta_details_advanced_send_get_roles_reminders_interval = {
                key: float(value)
                for key, value in (
                    raw_advanced_send_get_roles_reminders_interval.groupdict().items()
                )
                if value
            }

        cls._settings["ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL"] = (
            raw_timedelta_details_advanced_send_get_roles_reminders_interval
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
                for raw_statistics_role in raw_statistics_roles.split(",")
                if raw_statistics_role
            }

    @classmethod
    def _setup_moderation_document_url(cls) -> None:
        raw_moderation_document_url: str | None = os.getenv("MODERATION_DOCUMENT_URL")

        MODERATION_DOCUMENT_URL_IS_VALID: Final[bool] = bool(
            raw_moderation_document_url and validators.url(raw_moderation_document_url),
        )
        if not MODERATION_DOCUMENT_URL_IS_VALID:
            MODERATION_DOCUMENT_URL_MESSAGE: Final[str] = (
                "MODERATION_DOCUMENT_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(MODERATION_DOCUMENT_URL_MESSAGE)

        cls._settings["MODERATION_DOCUMENT_URL"] = raw_moderation_document_url

    @classmethod
    def _setup_strike_performed_manually_warning_location(cls) -> None:
        raw_strike_performed_manually_warning_location: str = os.getenv(
            "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION",
            "DM",
        )
        if not raw_strike_performed_manually_warning_location:
            STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION_MESSAGE: Final[str] = (
                "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION must be a valid name "
                "of a channel in your group's Discord guild."
            )
            raise ImproperlyConfiguredError(STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION_MESSAGE)

        cls._settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"] = (
            raw_strike_performed_manually_warning_location
        )

    @classmethod
    def _setup_auto_add_committee_to_threads(cls) -> None:
        raw_auto_add_committee_to_threads: str = str(
            os.getenv("AUTO_ADD_COMMITTEE_TO_THREADS", "True")
        ).lower()

        if raw_auto_add_committee_to_threads not in TRUE_VALUES | FALSE_VALUES:
            INVALID_AUTO_ADD_COMMITTEE_TO_THREADS_MESSAGE: Final[str] = (
                "AUTO_ADD_COMMITTEE_TO_THREADS must be a boolean value."
            )
            raise ImproperlyConfiguredError(INVALID_AUTO_ADD_COMMITTEE_TO_THREADS_MESSAGE)

        cls._settings["AUTO_ADD_COMMITTEE_TO_THREADS"] = (
            raw_auto_add_committee_to_threads in TRUE_VALUES
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

        webhook_config_logger: Logger = cls._setup_discord_log_channel_webhook()

        try:
            cls._setup_logging()
            cls._setup_discord_bot_token()
            cls._setup_discord_guild_id()
            cls._setup_group_full_name()
            cls._setup_group_short_name()
            cls._setup_ping_command_easter_egg_probability()
            cls._setup_welcome_messages()
            cls._setup_roles_messages()
            cls._setup_organisation_id()
            cls._setup_members_list_auth_session_cookie()
            cls._setup_membership_perks_url()
            cls._setup_purchase_membership_url()
            cls._setup_send_introduction_reminders()
            cls._setup_send_introduction_reminders_delay()
            cls._setup_send_introduction_reminders_interval()
            cls._setup_send_get_roles_reminders()
            cls._setup_send_get_roles_reminders_delay()
            cls._setup_advanced_send_get_roles_reminders_interval()
            cls._setup_statistics_days()
            cls._setup_statistics_roles()
            cls._setup_moderation_document_url()
            cls._setup_strike_performed_manually_warning_location()
            cls._setup_auto_add_committee_to_threads()
        except ImproperlyConfiguredError as improper_config_error:
            webhook_config_logger.error(improper_config_error.message)  # noqa: TRY400
            raise improper_config_error from improper_config_error

        cls._is_env_variables_setup = True


def _settings_class_factory() -> type[Settings]:
    @final
    class RuntimeSettings(Settings):
        """
        Settings class that provides access to all settings values.

        Settings values can be accessed via key (like a dictionary) or via class attribute.
        """

        _is_env_variables_setup: "ClassVar[bool]" = False
        _settings: "ClassVar[dict[str, object]]" = {}  # noqa: RUF012

    return RuntimeSettings


settings: "Final[Settings]" = _settings_class_factory()()


def run_setup() -> None:
    """Execute the required setup functions."""
    settings._setup_env_variables()  # noqa: SLF001

    logger.debug("Begin database setup")

    importlib.import_module("db")
    from django.core import management

    management.call_command("migrate")

    logger.debug("Database setup completed")
