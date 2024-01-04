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

import json
import logging
import os
import re
from collections.abc import Callable
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

    def __new__(cls, *args: object, **kwargs: object) -> "Settings":
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
        self._settings: dict[str, object] = {}

    def __getattr__(self, item: str) -> Any:  # type: ignore[misc]
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

    def __getitem__(self, item: str) -> Any:  # type: ignore[misc]
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
        if self._is_env_variables_setup:
            return

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
                "DISCORD_BOT_TOKEN must be a valid Discord bot token "
                "(see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)."
            )
            raise ImproperlyConfigured(INVALID_BOT_TOKEN_MESSAGE)
        self._settings["DISCORD_BOT_TOKEN"] = discord_bot_token

        discord_guild_id: str = os.getenv("DISCORD_GUILD_ID", "")
        if not discord_guild_id or not re.match(r"\A\d{17,20}\Z", discord_guild_id):
            INVALID_GUILD_ID_MESSAGE: Final[str] = (
                "DISCORD_GUILD_ID must be a valid Discord guild ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)."
            )
            raise ImproperlyConfigured(INVALID_GUILD_ID_MESSAGE)
        self._settings["DISCORD_GUILD_ID"] = int(discord_guild_id)

        discord_log_channel_webhook_url: str = os.getenv("DISCORD_LOG_CHANNEL_WEBHOOK_URL", "")
        discord_log_channel_webhook_url_is_valid: bool = bool(
            not discord_log_channel_webhook_url
            or (
                validators.url(discord_log_channel_webhook_url)
                and discord_log_channel_webhook_url.startswith(
                    "https://discord.com/api/webhooks/"
                )
            )
        )
        if not discord_log_channel_webhook_url_is_valid:
            INVALID_WEBHOOK_URL_MESSAGE: Final[str] = (
                "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL "
                "that points to a discord channel where logs should be displayed."
            )
            raise ImproperlyConfigured(INVALID_WEBHOOK_URL_MESSAGE)
        self._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = discord_log_channel_webhook_url

        group_full_name: str = os.getenv("GROUP_NAME", "")
        group_full_name_is_valid: bool = bool(
            not group_full_name
            or re.match(r"\A[A-Za-z0-9 '&!?:,.#%\"-]+\Z", group_full_name)
        )
        if not group_full_name_is_valid:
            INVALID_GROUP_FULL_NAME: Final[str] = (
                "GROUP_NAME must not contain any invalid characters."
            )
            raise ImproperlyConfigured(INVALID_GROUP_FULL_NAME)
        self._settings["_GROUP_FULL_NAME"] = group_full_name

        group_short_name: str = os.getenv("GROUP_SHORT_NAME", "")
        group_short_name_is_valid: bool = bool(
            not group_short_name
            or re.match(r"\A[A-Za-z0-9'&!?:,.#%\"-]+\Z", group_short_name)
        )
        if not group_short_name_is_valid:
            INVALID_GROUP_SHORT_NAME: Final[str] = (
                "GROUP_SHORT_NAME must not contain any invalid characters."
            )
            raise ImproperlyConfigured(INVALID_GROUP_SHORT_NAME)
        self._settings["_GROUP_SHORT_NAME"] = group_short_name

        purchase_membership_url: str = os.getenv("PURCHASE_MEMBERSHIP_URL", "")
        purchase_membership_url_is_valid: bool = bool(
            not purchase_membership_url
            or validators.url(purchase_membership_url)
        )
        if not purchase_membership_url_is_valid:
            INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE: Final[str] = (
                "PURCHASE_MEMBERSHIP_URL must be a valid URL."
            )
            raise ImproperlyConfigured(INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE)
        self._settings["PURCHASE_MEMBERSHIP_URL"] = purchase_membership_url

        membership_perks_url: str = os.getenv("MEMBERSHIP_PERKS_URL", "")
        membership_perks_url_is_valid: bool = bool(
            not membership_perks_url
            or validators.url(membership_perks_url)
        )
        if not membership_perks_url_is_valid:
            INVALID_MEMBERSHIP_PERKS_URL_MESSAGE: Final[str] = (
                "MEMBERSHIP_PERKS_URL must be a valid URL."
            )
            raise ImproperlyConfigured(INVALID_MEMBERSHIP_PERKS_URL_MESSAGE)
        self._settings["MEMBERSHIP_PERKS_URL"] = membership_perks_url

        try:
            ping_command_easter_egg_probability: float = 100 * float(
                os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01")
            )
        except ValueError as ping_command_easter_egg_probability_error:
            PROBABILITY_IS_NOT_FLOAT_MESSAGE: Final[str] = (
                "PING_COMMAND_EASTER_EGG_PROBABILITY must be a float."
            )
            raise ImproperlyConfigured(
                PROBABILITY_IS_NOT_FLOAT_MESSAGE
            ) from ping_command_easter_egg_probability_error
        if not 100 >= ping_command_easter_egg_probability >= 0:
            PROBABILITY_IS_NOT_IN_RANGE_MESSAGE: Final[str] = (
                "PING_COMMAND_EASTER_EGG_PROBABILITY must be a value "
                "between & including 1 & 0."
            )
            raise ImproperlyConfigured(PROBABILITY_IS_NOT_IN_RANGE_MESSAGE)
        self._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
            ping_command_easter_egg_probability
        )

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
                messages_dict: dict[object, object] = json.load(messages_file)
            except json.JSONDecodeError as messages_file_error:
                JSON_DECODING_ERROR_MESSAGE: Final[str] = (
                    "Messages JSON file must contain a JSON string that can be decoded "
                    "into a Python dict object."
                )
                raise ImproperlyConfigured(
                    JSON_DECODING_ERROR_MESSAGE
                ) from messages_file_error

        if "welcome_messages" not in messages_dict:
            raise MessagesJSONFileMissingKey(missing_key="welcome_messages")
        welcome_messages_key_is_valid: bool = bool(
            isinstance(messages_dict["welcome_messages"], list)
            and messages_dict["welcome_messages"]
        )
        if not welcome_messages_key_is_valid:
            raise MessagesJSONFileValueError(
                dict_key="welcome_messages",
                invalid_value=messages_dict["welcome_messages"]
            )
        self._settings["WELCOME_MESSAGES"] = messages_dict["welcome_messages"]

        if "roles_messages" not in messages_dict:
            raise MessagesJSONFileMissingKey(missing_key="roles_messages")
        roles_messages_key_is_valid: bool = bool(
            isinstance(messages_dict["roles_messages"], list)
            and messages_dict["roles_messages"]
        )
        if not roles_messages_key_is_valid:
            raise MessagesJSONFileValueError(
                dict_key="roles_messages",
                invalid_value=messages_dict["roles_messages"]
            )
        self._settings["ROLES_MESSAGES"] = messages_dict["roles_messages"]

        members_list_url: str = os.getenv("MEMBERS_LIST_URL", "")
        members_list_url_is_valid: bool = bool(
            members_list_url
            and validators.url(members_list_url)
        )
        if not members_list_url_is_valid:
            INVALID_MEMBERS_LIST_URL_MESSAGE: Final[str] = (
                "MEMBERS_LIST_URL must be a valid URL."
            )
            raise ImproperlyConfigured(INVALID_MEMBERS_LIST_URL_MESSAGE)
        self._settings["MEMBERS_LIST_URL"] = members_list_url

        members_list_url_session_cookie: str = os.getenv("MEMBERS_LIST_URL_SESSION_COOKIE", "")
        members_list_url_session_cookie_is_valid: bool = bool(
            members_list_url_session_cookie
            and re.match(r"\A[A-Fa-f\d]{128,256}\Z", members_list_url_session_cookie)
        )
        if not members_list_url_session_cookie_is_valid:
            INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE: Final[str] = (
                "MEMBERS_LIST_URL_SESSION_COOKIE must be a valid .ASPXAUTH cookie."
            )
            raise ImproperlyConfigured(INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE)
        self._settings["MEMBERS_LIST_URL_SESSION_COOKIE"] = members_list_url_session_cookie

        send_introduction_reminders: str = str(
            os.getenv("SEND_INTRODUCTION_REMINDERS", "Once")
        ).lower()
        if send_introduction_reminders not in VALID_SEND_INTRODUCTION_REMINDERS_VALUES:
            INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE: Final[str] = (
                "SEND_INTRODUCTION_REMINDERS must be one of: "
                "\"Once\", \"Interval\" or \"False\"."
            )
            raise ImproperlyConfigured(INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE)
        if send_introduction_reminders in ("once", "interval"):
            self._settings["SEND_INTRODUCTION_REMINDERS"] = send_introduction_reminders
        elif send_introduction_reminders in TRUE_VALUES:
            self._settings["SEND_INTRODUCTION_REMINDERS"] = "once"
        else:
            self._settings["SEND_INTRODUCTION_REMINDERS"] = False

        raw_send_introduction_reminders_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("SEND_INTRODUCTION_REMINDERS_INTERVAL", "6h"))
        )
        if self._settings["SEND_INTRODUCTION_REMINDERS"]:
            if not raw_send_introduction_reminders_interval:
                INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
                    "SEND_INTRODUCTION_REMINDERS_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfigured(
                    INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE
                )
            self._settings["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = {
                key: float(value)
                for key, value
                in raw_send_introduction_reminders_interval.groupdict().items()
                if value
            }
        else:
            self._settings["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = {"hours": 6}

        kick_no_introduction_discord_members: str = str(
            os.getenv("KICK_NO_INTRODUCTION_DISCORD_MEMBERS", "False")
        ).lower()
        if kick_no_introduction_discord_members not in TRUE_VALUES | FALSE_VALUES:
            INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_MESSAGE: Final[str] = (
                "KICK_NO_INTRODUCTION_DISCORD_MEMBERS must be a boolean value."
            )
            raise ImproperlyConfigured(
                INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_MESSAGE
            )
        self._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS"] = (
            kick_no_introduction_discord_members in TRUE_VALUES
        )

        raw_kick_no_introduction_discord_members_delay: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
            str(os.getenv("KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY", "5d"))
        )
        if self._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS"]:
            if not raw_kick_no_introduction_discord_members_delay:
                INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE: Final[str] = (
                    "KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY must contain the delay "
                    "in any combination of seconds, minutes, hours, days or weeks."
                )
                raise ImproperlyConfigured(
                    INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE
                )
            kick_no_introduction_discord_members_delay: timedelta = timedelta(
                **{
                    key: float(value)
                    for key, value
                    in raw_kick_no_introduction_discord_members_delay.groupdict().items()
                    if value
                }
            )
            if kick_no_introduction_discord_members_delay <= timedelta(days=1):
                TOO_SMALL_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE: Final[str] = (
                    "KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY "
                    "must be greater than 1 day."
                )
                raise ImproperlyConfigured(
                    TOO_SMALL_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY_MESSAGE
                )
            self._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY"] = (
                kick_no_introduction_discord_members_delay
            )
        else:
            self._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY"] = timedelta()

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

        raw_send_get_roles_reminders_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            str(os.getenv("SEND_GET_ROLES_REMINDERS_INTERVAL", "24h"))
        )
        if self._settings["SEND_GET_ROLES_REMINDERS"]:
            if not raw_send_get_roles_reminders_interval:
                INVALID_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
                    "SEND_GET_ROLES_REMINDERS_INTERVAL must contain the interval "
                    "in any combination of seconds, minutes or hours."
                )
                raise ImproperlyConfigured(
                    INVALID_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE
                )
            self._settings["SEND_GET_ROLES_REMINDERS_INTERVAL"] = {
                key: float(value)
                for key, value
                in raw_send_get_roles_reminders_interval.groupdict().items()
                if value
            }
        else:
            self._settings["SEND_GET_ROLES_REMINDERS_INTERVAL"] = {"hours": 24}

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
            } or {LOG_LEVEL_CHOICES[-1]!r}."""
            raise ImproperlyConfigured(INVALID_LOG_LEVEL_MESSAGE)
        # noinspection SpellCheckingInspection
        logging.basicConfig(
            level=getattr(logging, console_log_level),
            format="%(levelname)s: %(message)s"
        )

        moderation_document_url: str = os.getenv("MODERATION_DOCUMENT_URL", "")
        moderation_document_url_is_valid: bool = bool(
            moderation_document_url
            and validators.url(moderation_document_url)
        )
        if not moderation_document_url_is_valid:
            INVALID_MODERATION_DOCUMENT_URL_MESSAGE: Final[str] = (
                "MODERATION_DOCUMENT_URL must be a valid URL."
            )
            raise ImproperlyConfigured(INVALID_MODERATION_DOCUMENT_URL_MESSAGE)
        self._settings["MODERATION_DOCUMENT_URL"] = moderation_document_url

        manual_moderation_warning_message_location: str = os.getenv(
            "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION",
            "DM"
        )
        if not manual_moderation_warning_message_location:
            INVALID_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE: Final[str] = (
                "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION must be a valid name "
                "of a channel in the your group's Discord guild."
            )
            raise ImproperlyConfigured(
                INVALID_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE
            )
        self._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = (
            manual_moderation_warning_message_location
        )

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
