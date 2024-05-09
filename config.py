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
    "run_setup",
    "Settings",
    "settings",
)


import abc
import functools
import importlib
import json
import logging
import os
import re
from collections.abc import Iterable, Mapping
from datetime import timedelta
from logging import Logger
from pathlib import Path
from re import Match
from typing import IO, Any, ClassVar, Final

import dotenv
import regex
import validators

from exceptions import (
    ImproperlyConfiguredError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)

PROJECT_ROOT: Final[Path] = Path(__file__).parent.resolve()

TRUE_VALUES: Final[frozenset[str]] = frozenset({"true", "1", "t", "y", "yes", "on"})
FALSE_VALUES: Final[frozenset[str]] = frozenset({"false", "0", "f", "n", "no", "off"})
VALID_SEND_INTRODUCTION_REMINDERS_VALUES: Final[frozenset[str]] = frozenset(
    {"once", "interval"} | TRUE_VALUES | FALSE_VALUES,
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
        "Quiz Victor",
    },
)
LOG_LEVEL_CHOICES: Final[Sequence[str]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)


logger: Logger = logging.getLogger("TeX-Bot")


class Settings(abc.ABC):
    """
    Settings class that provides access to all settings values.

    Settings values can be accessed via key (like a dictionary) or via class attribute.
    """

    _is_env_variables_setup: ClassVar[bool]
    _settings: ClassVar[dict[str, object]]

    @classmethod
    def get_invalid_settings_key_message_for_item_name(cls, item_name: str) -> str:
        """Return the message to state that the given settings key is invalid."""
        return f"{item_name!r} is not a valid settings key."

    def __getattr__(self, item: str) -> Any:  # type: ignore[misc]  # noqa: ANN401
        """Retrieve settings value by attribute lookup."""
        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

        if "_pytest" in item or item in ("__bases__", "__test__"):  # NOTE: Overriding __getattr__() leads to many edge-case issues where external libraries will attempt to call getattr() with peculiar values
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if not self._is_env_variables_setup:
            self._setup_env_variables()

        if item in self._settings:
            return self._settings[item]

        if re.match(r"\A(?!_)(?:(?!_{2,})[A-Z_])+(?<!_)\Z", item):
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = self.get_invalid_settings_key_message_for_item_name(  # noqa: E501
                item,
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

    def __getitem__(self, item: str) -> Any:  # type: ignore[misc]  # noqa: ANN401
        """Retrieve settings value by key lookup."""
        e: AttributeError
        try:
            return getattr(self, item)
        except AttributeError as e:
            key_error_message: str = item

            if self.get_invalid_settings_key_message_for_item_name(item) in str(e):
                key_error_message = str(e)

            raise KeyError(key_error_message) from None

    @classmethod
    def _setup_logging(cls) -> None:
        raw_console_log_level: str | None = os.getenv("CONSOLE_LOG_LEVEL")
        console_log_level: str = (
            "INFO"
            if raw_console_log_level is None
            else (
                raw_console_log_level.upper().strip()
                if raw_console_log_level.upper().strip()
                else raw_console_log_level
            )
        )

        if console_log_level not in LOG_LEVEL_CHOICES:
            INVALID_LOG_LEVEL_MESSAGE: Final[str] = f"""LOG_LEVEL must be one of {
                    ",".join(
                        f"{log_level_choice!r}"
                        for log_level_choice
                        in LOG_LEVEL_CHOICES[:-1]
                    )
                } or {LOG_LEVEL_CHOICES[-1]!r}."""
            raise ImproperlyConfiguredError(INVALID_LOG_LEVEL_MESSAGE)

        logger.setLevel(getattr(logging, console_log_level))

        console_logging_handler: logging.Handler = logging.StreamHandler()
        # noinspection SpellCheckingInspection
        console_logging_handler.setFormatter(
            logging.Formatter("[{asctime}] {name} | {levelname:^8} - {message}", style="{"),
        )

        logging.getLogger("").addHandler(console_logging_handler)

    @classmethod
    def _setup_discord_bot_token(cls) -> None:
        raw_discord_bot_token: str | None = os.getenv("DISCORD_BOT_TOKEN")

        DISCORD_BOT_TOKEN_IS_VALID: Final[bool] = bool(
            raw_discord_bot_token is not None
            and raw_discord_bot_token.strip()
            and re.match(
                r"\A[A-Za-z0-9]{24,26}\.[A-Za-z0-9]{6}\.[A-Za-z0-9_-]{27,38}\Z",
                raw_discord_bot_token.strip(),
            ),
        )
        if not DISCORD_BOT_TOKEN_IS_VALID:
            INVALID_DISCORD_BOT_TOKEN_MESSAGE: Final[str] = (
                "DISCORD_BOT_TOKEN must be a valid Discord bot token "
                "(see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_BOT_TOKEN_MESSAGE)

        cls._settings["DISCORD_BOT_TOKEN"] = raw_discord_bot_token.strip()  # type: ignore[union-attr]

    @classmethod
    def _setup_discord_log_channel_webhook_url(cls) -> None:
        raw_discord_log_channel_webhook_url: str | None = os.getenv(
           "DISCORD_LOG_CHANNEL_WEBHOOK_URL",
        )

        DISCORD_LOG_CHANNEL_WEBHOOK_URL_IS_VALID: Final[bool] = bool(
            raw_discord_log_channel_webhook_url is None
            or (
                raw_discord_log_channel_webhook_url.strip()
                and re.match(
                    r"\Ahttps://discord.com/api/webhooks/\d{17,20}/[a-zA-Z\d]{60,90}/?\Z",
                    raw_discord_log_channel_webhook_url.strip(),
                )
                and validators.url(raw_discord_log_channel_webhook_url.strip())
            ),
        )
        if not DISCORD_LOG_CHANNEL_WEBHOOK_URL_IS_VALID:
            INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE: Final[str] = (
                "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL "
                "that points to a discord channel where logs should be displayed."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE)

        cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = (
            raw_discord_log_channel_webhook_url.strip()
            if raw_discord_log_channel_webhook_url is not None
            else raw_discord_log_channel_webhook_url
        )

    @classmethod
    def _setup_discord_guild_id(cls) -> None:
        raw_discord_guild_id: str | None = os.getenv("DISCORD_GUILD_ID")

        DISCORD_GUILD_ID_IS_VALID: Final[bool] = bool(
            raw_discord_guild_id is not None
            and raw_discord_guild_id.strip()
            and re.match(r"\A\d{17,20}\Z", raw_discord_guild_id.strip()),
        )
        if not DISCORD_GUILD_ID_IS_VALID:
            INVALID_DISCORD_GUILD_ID_MESSAGE: Final[str] = (
                "DISCORD_GUILD_ID must be a valid Discord guild ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)."
            )
            raise ImproperlyConfiguredError(INVALID_DISCORD_GUILD_ID_MESSAGE)

        cls._settings["DISCORD_GUILD_ID"] = int(raw_discord_guild_id.strip())  # type: ignore[union-attr]

    @classmethod
    def _setup_group_full_name(cls) -> None:
        raw_group_full_name: str | None = os.getenv("GROUP_NAME")

        if raw_group_full_name is not None:
            raw_group_full_name = raw_group_full_name.translate(
                {
                    ord(unicode_char): ascii_char
                    for unicode_char, ascii_char
                    in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
                },
            )

        GROUP_FULL_NAME_IS_VALID: Final[bool] = bool(
            raw_group_full_name is None
            or (
                raw_group_full_name.strip()
                and regex.match(  # NOTE: The `regex` package is used here instead of python's in-built `re` package, because the `regex` package supports matching Unicode character classes (E.g. `\p{L}`)
                    r"\A(?![ &!?:,.%-])(?:(?!['()&:,.#%\"-]{2,}| {2,})[\p{L}\p{M}0-9 '()&!?:,.#%\"-])*(?<![ &,-])\Z",  # noqa: E501
                    raw_group_full_name.strip(),
                )
                and regex.search(r"\p{L}", raw_group_full_name.strip())  # NOTE: The `regex` package is used here instead of python's in-built `re` package, because the `regex` package supports matching Unicode character classes (E.g. `\p{L}`)
            ),
        )
        if not GROUP_FULL_NAME_IS_VALID:
            INVALID_GROUP_FULL_NAME: Final[str] = (
                "GROUP_NAME must not contain any invalid characters."
            )
            raise ImproperlyConfiguredError(INVALID_GROUP_FULL_NAME)

        cls._settings["_GROUP_FULL_NAME"] = (
            raw_group_full_name.strip()
            if raw_group_full_name is not None
            else raw_group_full_name
        )

    @classmethod
    def _setup_group_short_name(cls) -> None:
        raw_group_short_name: str | None = os.getenv("GROUP_SHORT_NAME")

        GROUP_SHORT_NAME_CAN_BE_RESOLVED_FROM_GROUP_FULL_NAME: Final[bool] = bool(
            raw_group_short_name is None
            and "_GROUP_FULL_NAME" in cls._settings
            and cls._settings["_GROUP_FULL_NAME"] is not None,
        )
        if GROUP_SHORT_NAME_CAN_BE_RESOLVED_FROM_GROUP_FULL_NAME:
            raw_group_short_name = (
                "CSS"
                if (
                    "_GROUP_FULL_NAME" in cls._settings
                    and cls._settings["_GROUP_FULL_NAME"] is not None
                    and (
                        "computer science society" in cls._settings["_GROUP_FULL_NAME"].lower()  # type: ignore[attr-defined]
                        or "css" in cls._settings["_GROUP_FULL_NAME"].lower()  # type: ignore[attr-defined]
                    )
                )
                else cls._settings["_GROUP_FULL_NAME"]
            ).replace(
                "the",
                "",
            ).replace(
                "THE",
                "",
            ).replace(
                "The",
                "",
            ).replace(
                " ",
                "",
            ).replace(
                "\t",
                "",
            ).replace(
                "\n",
                "",
            ).strip()

        if raw_group_short_name is not None:
            raw_group_short_name = raw_group_short_name.translate(
                {
                    ord(unicode_char): ascii_char
                    for unicode_char, ascii_char
                    in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
                },
            )

        GROUP_SHORT_NAME_IS_VALID: Final[bool] = bool(
            raw_group_short_name is None
            or (
                raw_group_short_name.strip()
                and regex.match(  # NOTE: The `regex` package is used here instead of python's in-built `re` package, because the `regex` package supports matching Unicode character classes (E.g. `\p{L}`)
                    r"\A(?![&!?:,.%-])(?:(?!['()&:,.#%\"-]{2,})[\p{L}\p{M}0-9'()&!?:,.#%\"-])*(?<![&,-])\Z",
                    raw_group_short_name.strip(),
                )
                and regex.search(r"\p{L}", raw_group_short_name.strip())  # NOTE: The `regex` package is used here instead of python's in-built `re` package, because the `regex` package supports matching Unicode character classes (E.g. `\p{L}`)
            ),
        )
        if not GROUP_SHORT_NAME_IS_VALID:
            INVALID_GROUP_SHORT_NAME: Final[str] = (
                "GROUP_SHORT_NAME must not contain any invalid characters."
            )
            raise ImproperlyConfiguredError(INVALID_GROUP_SHORT_NAME)

        cls._settings["_GROUP_SHORT_NAME"] = (
            raw_group_short_name.strip()
            if raw_group_short_name is not None
            else raw_group_short_name
        )

    @classmethod
    def _setup_purchase_membership_url(cls) -> None:
        raw_purchase_membership_url: str | None = os.getenv("PURCHASE_MEMBERSHIP_URL")

        RAW_PURCHASE_MEMBERSHIP_URL_HAS_NO_SCHEME: Final[bool] = bool(
            raw_purchase_membership_url is not None
            and "://" not in raw_purchase_membership_url.strip(),
        )
        if RAW_PURCHASE_MEMBERSHIP_URL_HAS_NO_SCHEME:
            raw_purchase_membership_url = f"https://{raw_purchase_membership_url.strip()}"  # type: ignore[union-attr]

        PURCHASE_MEMBERSHIP_URL_IS_VALID: Final[bool] = bool(
            raw_purchase_membership_url is None
            or (
                raw_purchase_membership_url.strip()
                and validators.url(raw_purchase_membership_url.strip())
            ),
        )
        if not PURCHASE_MEMBERSHIP_URL_IS_VALID:
            INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE: Final[str] = (
                "PURCHASE_MEMBERSHIP_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE)

        cls._settings["PURCHASE_MEMBERSHIP_URL"] = (
            raw_purchase_membership_url.strip()
            if raw_purchase_membership_url is not None
            else raw_purchase_membership_url
        )

    @classmethod
    def _setup_membership_perks_url(cls) -> None:
        raw_membership_perks_url: str | None = os.getenv("MEMBERSHIP_PERKS_URL")

        RAW_MEMBERSHIP_PERKS_URL_HAS_NO_SCHEME: Final[bool] = bool(
            raw_membership_perks_url is not None
            and "://" not in raw_membership_perks_url.strip(),
        )
        if RAW_MEMBERSHIP_PERKS_URL_HAS_NO_SCHEME:
            raw_membership_perks_url = f"https://{raw_membership_perks_url.strip()}"  # type: ignore[union-attr]

        MEMBERSHIP_PERKS_URL_IS_VALID: Final[bool] = bool(
            raw_membership_perks_url is None
            or (
                raw_membership_perks_url.strip()
                and validators.url(raw_membership_perks_url.strip())
            ),
        )
        if not MEMBERSHIP_PERKS_URL_IS_VALID:
            INVALID_MEMBERSHIP_PERKS_URL_MESSAGE: Final[str] = (
                "MEMBERSHIP_PERKS_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERSHIP_PERKS_URL_MESSAGE)

        cls._settings["MEMBERSHIP_PERKS_URL"] = (
            raw_membership_perks_url.strip()
            if raw_membership_perks_url is not None
            else raw_membership_perks_url
        )

    @classmethod
    def _setup_ping_command_easter_egg_probability(cls) -> None:
        INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE: Final[str] = (
            "PING_COMMAND_EASTER_EGG_PROBABILITY must be a float between & including 1 & 0."
        )

        raw_ping_command_easter_egg_probability: str | None = (
            os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY")
        )

        e: ValueError
        try:
            ping_command_easter_egg_probability: float = 100 * (
                0.01
                if raw_ping_command_easter_egg_probability is None
                else (
                    float(raw_ping_command_easter_egg_probability.strip())
                    if raw_ping_command_easter_egg_probability.strip()
                    else float(raw_ping_command_easter_egg_probability)
                )
            )
        except ValueError as e:
            raise (
                ImproperlyConfiguredError(INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE)
            ) from e

        if not 0 <= ping_command_easter_egg_probability <= 100:
            raise ImproperlyConfiguredError(
                INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE,
            )

        cls._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
            ping_command_easter_egg_probability
        )

    @classmethod
    @functools.lru_cache(maxsize=5)
    def _get_messages_dict(cls, raw_messages_file_path: str | None) -> Mapping[str, object]:
        JSON_DECODING_ERROR_MESSAGE: Final[str] = (
            "Messages JSON file must contain a JSON string that can be decoded "
            "into a Python dict object."
        )
        MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE: Final[str] = (
            "MESSAGES_FILE_PATH must be a path to a file that exists."
        )

        if raw_messages_file_path is not None and not raw_messages_file_path.strip():
            raise ImproperlyConfiguredError(MESSAGES_FILE_PATH_DOES_NOT_EXIST_MESSAGE)

        messages_file_path: Path = (
            Path(raw_messages_file_path.strip())
            if raw_messages_file_path is not None
            else PROJECT_ROOT / Path("messages.json")
        )

        if not messages_file_path.is_file():
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

        ROLES_MESSAGES_KEY_IS_VALID: Final[bool] = bool(
            isinstance(messages_dict["roles_messages"], Iterable)
            and messages_dict["roles_messages"],
        )
        if not ROLES_MESSAGES_KEY_IS_VALID:
            raise MessagesJSONFileValueError(
                dict_key="roles_messages",
                invalid_value=messages_dict["roles_messages"],
            )
        cls._settings["ROLES_MESSAGES"] = set(messages_dict["roles_messages"])  # type: ignore[call-overload]

    @classmethod
    def _setup_members_list_url(cls) -> None:
        raw_members_list_url: str | None = os.getenv("MEMBERS_LIST_URL")

        RAW_MEMBERS_LIST_URL_HAS_NO_SCHEME: Final[bool] = bool(
            raw_members_list_url is not None and "://" not in raw_members_list_url.strip(),
        )
        if RAW_MEMBERS_LIST_URL_HAS_NO_SCHEME:
            raw_members_list_url = f"https://{raw_members_list_url.strip()}"  # type: ignore[union-attr]

        MEMBERS_LIST_URL_IS_VALID: Final[bool] = bool(
            raw_members_list_url is not None
            and raw_members_list_url.strip()
            and validators.url(raw_members_list_url.strip()),
        )
        if not MEMBERS_LIST_URL_IS_VALID:
            INVALID_MEMBERS_LIST_URL_MESSAGE: Final[str] = (
                "MEMBERS_LIST_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERS_LIST_URL_MESSAGE)

        cls._settings["MEMBERS_LIST_URL"] = raw_members_list_url.strip()  # type: ignore[union-attr]

    @classmethod
    def _setup_members_list_url_session_cookie(cls) -> None:
        raw_members_list_url_session_cookie: str | None = os.getenv(
            "MEMBERS_LIST_URL_SESSION_COOKIE",
        )

        MEMBERS_LIST_URL_SESSION_COOKIE_IS_VALID: Final[bool] = bool(
            raw_members_list_url_session_cookie is not None
            and raw_members_list_url_session_cookie.strip()
            and re.match(
                r"\A[A-Fa-f\d]{128,256}\Z",
                raw_members_list_url_session_cookie.strip(),
            ),
        )
        if not MEMBERS_LIST_URL_SESSION_COOKIE_IS_VALID:
            INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE: Final[str] = (
                "MEMBERS_LIST_URL_SESSION_COOKIE must be a valid .ASPXAUTH cookie."
            )
            raise ImproperlyConfiguredError(INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE)

        cls._settings["MEMBERS_LIST_URL_SESSION_COOKIE"] = (
            raw_members_list_url_session_cookie.strip()  # type: ignore[union-attr]
        )

    @classmethod
    def _setup_send_introduction_reminders(cls) -> None:
        raw_send_introduction_reminders: str | None = os.getenv("SEND_INTRODUCTION_REMINDERS")

        # noinspection PyTypeChecker
        send_introduction_reminders: str | bool = (
            "Once".lower().strip()
            if raw_send_introduction_reminders is None
            else (
                raw_send_introduction_reminders.lower().strip()
                if raw_send_introduction_reminders.lower().strip()
                else raw_send_introduction_reminders
            )
        )

        if send_introduction_reminders not in VALID_SEND_INTRODUCTION_REMINDERS_VALUES:
            INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE: Final[str] = (
                "SEND_INTRODUCTION_REMINDERS must be one of: "
                "\"Once\", \"Interval\" or \"False\"."
            )
            raise ImproperlyConfiguredError(INVALID_SEND_INTRODUCTION_REMINDERS_MESSAGE)

        cls._settings["SEND_INTRODUCTION_REMINDERS"] = (
            "once"
            if send_introduction_reminders in TRUE_VALUES
            else (
                False
                if send_introduction_reminders not in ("once", "interval")
                else send_introduction_reminders
            )
        )

    @classmethod
    def _error_setup_send_introduction_reminders_interval(cls, msg: str | None = None) -> None:
        if cls._settings["SEND_INTRODUCTION_REMINDERS"]:
            msg = msg if msg is not None else (
                "SEND_INTRODUCTION_REMINDERS_INTERVAL must contain the interval "
                "in any combination of seconds, minutes or hours."
            )
            raise ImproperlyConfiguredError(msg)

        cls._settings["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = {"hours": 6}

    @classmethod
    def _setup_send_introduction_reminders_interval(cls) -> None:
        if "SEND_INTRODUCTION_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_INTRODUCTION_REMINDERS must be set up "
                "before SEND_INTRODUCTION_REMINDERS_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_send_introduction_reminders_interval: str | None = (
            os.getenv("SEND_INTRODUCTION_REMINDERS_INTERVAL")
        )

        send_introduction_reminders_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)\s*s)?\s*(?:(?P<minutes>(?:\d*\.)?\d+)\s*m)?\s*(?:(?P<hours>(?:\d*\.)?\d+)\s*h)?\Z",
            (
                "6h"
                if raw_send_introduction_reminders_interval is None
                else (
                    raw_send_introduction_reminders_interval.lower().strip()
                    if raw_send_introduction_reminders_interval.lower().strip()
                    else raw_send_introduction_reminders_interval
                )
            ),
        )

        if send_introduction_reminders_interval is None:
            cls._error_setup_send_introduction_reminders_interval()
            return

        details_send_introduction_reminders_interval: dict[str, float] = {
            key: float(value)
            for key, value
            in send_introduction_reminders_interval.groupdict().items()
            if value
        }

        if not details_send_introduction_reminders_interval:
            cls._error_setup_send_introduction_reminders_interval()
            return

        if timedelta(**details_send_introduction_reminders_interval) <= timedelta(seconds=3):
            cls._error_setup_send_introduction_reminders_interval(
                msg="SEND_INTRODUCTION_REMINDERS_INTERVAL must be greater than 3 seconds.",
            )
            return

        cls._settings["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
            details_send_introduction_reminders_interval
        )

    @classmethod
    def _setup_kick_no_introduction_discord_members(cls) -> None:
        raw_kick_no_introduction_discord_members: str | None = (
            os.getenv("KICK_NO_INTRODUCTION_DISCORD_MEMBERS")
        )

        KICK_NO_INTRODUCTION_DISCORD_MEMBERS_IS_VALID: Final[bool] = bool(
            raw_kick_no_introduction_discord_members is None
            or (
                raw_kick_no_introduction_discord_members.lower().strip()
                in TRUE_VALUES | FALSE_VALUES
            ),
        )
        if not KICK_NO_INTRODUCTION_DISCORD_MEMBERS_IS_VALID:
            INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_MESSAGE: Final[str] = (
                "KICK_NO_INTRODUCTION_DISCORD_MEMBERS must be a boolean value."
            )
            raise ImproperlyConfiguredError(
                INVALID_KICK_NO_INTRODUCTION_DISCORD_MEMBERS_MESSAGE,
            )

        cls._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS"] = (
            False
            if raw_kick_no_introduction_discord_members is None
            else raw_kick_no_introduction_discord_members.lower().strip() in TRUE_VALUES
        )

    @classmethod
    def _error_setup_kick_no_introduction_discord_members_delay(cls, msg: str | None = None) -> None:  # noqa: E501
        if cls._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS"]:
            msg = msg if msg is not None else (
                "KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY must contain the delay "
                "in any combination of seconds, minutes, hours, days or weeks."
            )
            raise ImproperlyConfiguredError(msg)

        cls._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY"] = timedelta()

    @classmethod
    def _setup_kick_no_introduction_discord_members_delay(cls) -> None:
        if "KICK_NO_INTRODUCTION_DISCORD_MEMBERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: KICK_NO_INTRODUCTION_DISCORD_MEMBERS must be set up "
                "before KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_kick_no_introduction_discord_members_delay: str | None = (
            os.getenv("KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY")
        )

        kick_no_introduction_discord_members_delay: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)\s*s)?\s*(?:(?P<minutes>(?:\d*\.)?\d+)\s*m)?\s*(?:(?P<hours>(?:\d*\.)?\d+)\s*h)?\s*(?:(?P<days>(?:\d*\.)?\d+)\s*d)?\s*(?:(?P<weeks>(?:\d*\.)?\d+)\s*w)?\Z",
            (
                "5d"
                if raw_kick_no_introduction_discord_members_delay is None
                else (
                    raw_kick_no_introduction_discord_members_delay.lower().strip()
                    if raw_kick_no_introduction_discord_members_delay.lower().strip()
                    else raw_kick_no_introduction_discord_members_delay
                )
            ),
        )

        if kick_no_introduction_discord_members_delay is None:
            cls._error_setup_kick_no_introduction_discord_members_delay()
            return

        details_kick_no_introduction_discord_members_delay: dict[str, float] = {
            key: float(value)
            for key, value
            in kick_no_introduction_discord_members_delay.groupdict().items()
            if value
        }

        if not details_kick_no_introduction_discord_members_delay:
            cls._error_setup_kick_no_introduction_discord_members_delay()
            return

        timedelta_kick_no_introduction_discord_members_delay: timedelta = timedelta(
            **details_kick_no_introduction_discord_members_delay,
        )

        if timedelta_kick_no_introduction_discord_members_delay <= timedelta(days=1):
            cls._error_setup_kick_no_introduction_discord_members_delay(
                msg="KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY must be greater than 1 day.",
            )
            return

        cls._settings["KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY"] = (
            timedelta_kick_no_introduction_discord_members_delay
        )

    @classmethod
    def _setup_send_get_roles_reminders(cls) -> None:
        raw_send_get_roles_reminders: str | None = (
            os.getenv("SEND_GET_ROLES_REMINDERS")
        )

        SEND_GET_ROLES_REMINDERS_IS_VALID: Final[bool] = bool(
            raw_send_get_roles_reminders is None
            or raw_send_get_roles_reminders.lower().strip() in TRUE_VALUES | FALSE_VALUES,
        )
        if not SEND_GET_ROLES_REMINDERS_IS_VALID:
            INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE: Final[str] = (
                "SEND_GET_ROLES_REMINDERS must be a boolean value."
            )
            raise ImproperlyConfiguredError(
                INVALID_SEND_GET_ROLES_REMINDERS_MESSAGE,
            )

        cls._settings["SEND_GET_ROLES_REMINDERS"] = (
            True
            if raw_send_get_roles_reminders is None
            else raw_send_get_roles_reminders.lower().strip() in TRUE_VALUES
        )

    @classmethod
    def _error_setup_send_get_roles_reminders_interval(cls, msg: str | None = None) -> None:
        if cls._settings["SEND_GET_ROLES_REMINDERS"]:
            msg = msg if msg is not None else (
                "SEND_GET_ROLES_REMINDERS_INTERVAL must contain the interval "
                "in any combination of seconds, minutes or hours."
            )
            raise ImproperlyConfiguredError(msg)

        cls._settings["SEND_GET_ROLES_REMINDERS_INTERVAL"] = {"hours": 24}

    @classmethod
    def _setup_send_get_roles_reminders_interval(cls) -> None:
        if "SEND_GET_ROLES_REMINDERS" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: SEND_GET_ROLES_REMINDERS must be set up "
                "before SEND_GET_ROLES_REMINDERS_INTERVAL can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_send_get_roles_reminders_interval: str | None = (
            os.getenv("SEND_GET_ROLES_REMINDERS_INTERVAL")
        )

        send_get_roles_reminders_interval: Match[str] | None = re.match(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)\s*s)?\s*(?:(?P<minutes>(?:\d*\.)?\d+)\s*m)?\s*(?:(?P<hours>(?:\d*\.)?\d+)\s*h)?\Z",
            (
                "24h"
                if raw_send_get_roles_reminders_interval is None
                else (
                    raw_send_get_roles_reminders_interval.lower().strip()
                    if raw_send_get_roles_reminders_interval.lower().strip()
                    else raw_send_get_roles_reminders_interval
                )
            ),
        )

        if send_get_roles_reminders_interval is None:
            cls._error_setup_send_get_roles_reminders_interval()
            return

        details_send_get_roles_reminders_interval: dict[str, float] = {
            key: float(value)
            for key, value
            in send_get_roles_reminders_interval.groupdict().items()
            if value
        }

        if not details_send_get_roles_reminders_interval:
            cls._error_setup_send_get_roles_reminders_interval()
            return

        if timedelta(**details_send_get_roles_reminders_interval) <= timedelta(seconds=3):
            cls._error_setup_send_get_roles_reminders_interval(
                msg="SEND_GET_ROLES_REMINDERS_INTERVAL must be greater than 3 seconds.",
            )
            return

        cls._settings["SEND_GET_ROLES_REMINDERS_INTERVAL"] = (
            details_send_get_roles_reminders_interval
        )

    @classmethod
    def _setup_statistics_days(cls) -> None:
        raw_statistics_days: str | None = os.getenv("STATISTICS_DAYS")

        e: ValueError
        try:
            statistics_days: float = (
                30 if raw_statistics_days is None else float(raw_statistics_days.strip())
            )
        except ValueError as e:
            INVALID_STATISTICS_DAYS_MESSAGE: Final[str] = (
                "STATISTICS_DAYS must contain the statistics period in days."
            )
            raise ImproperlyConfiguredError(INVALID_STATISTICS_DAYS_MESSAGE) from e

        if statistics_days <= 1:
            TOO_SMALL_STATISTICS_DAYS_MESSAGE: Final[str] = (
                "STATISTICS_DAYS cannot be less than (or equal to) 1 day."
            )
            raise ImproperlyConfiguredError(TOO_SMALL_STATISTICS_DAYS_MESSAGE)

        cls._settings["STATISTICS_DAYS"] = timedelta(days=statistics_days)

    @classmethod
    def _setup_statistics_roles(cls) -> None:
        raw_statistics_roles: str | None = os.getenv("STATISTICS_ROLES")

        if raw_statistics_roles is None:
            cls._settings["STATISTICS_ROLES"] = DEFAULT_STATISTICS_ROLES

        else:
            cls._settings["STATISTICS_ROLES"] = {
                raw_statistics_role.strip()
                for raw_statistics_role
                in raw_statistics_roles.strip().split(",")
                if raw_statistics_role.strip()
            }

    @classmethod
    def _setup_moderation_document_url(cls) -> None:
        raw_moderation_document_url: str | None = os.getenv("MODERATION_DOCUMENT_URL")

        RAW_MODERATION_DOCUMENT_URL_HAS_NO_SCHEME: Final[bool] = bool(
            raw_moderation_document_url is not None
            and "://" not in raw_moderation_document_url.strip(),
        )
        if RAW_MODERATION_DOCUMENT_URL_HAS_NO_SCHEME:
            raw_moderation_document_url = f"https://{raw_moderation_document_url.strip()}"  # type: ignore[union-attr]

        MODERATION_DOCUMENT_URL_IS_VALID: Final[bool] = bool(
            raw_moderation_document_url is not None
            and raw_moderation_document_url.strip()
            and validators.url(raw_moderation_document_url.strip()),
        )
        if not MODERATION_DOCUMENT_URL_IS_VALID:
            MODERATION_DOCUMENT_URL_MESSAGE: Final[str] = (
                "MODERATION_DOCUMENT_URL must be a valid URL."
            )
            raise ImproperlyConfiguredError(MODERATION_DOCUMENT_URL_MESSAGE)

        cls._settings["MODERATION_DOCUMENT_URL"] = raw_moderation_document_url.strip()  # type: ignore[union-attr]

    @classmethod
    def _setup_manual_moderation_warning_message_location(cls) -> None:
        raw_manual_moderation_warning_message_location: str | None = (
            os.getenv("MANUAL_MODERATION_WARNING_MESSAGE_LOCATION")
        )

        MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_IS_VALID: Final[bool] = bool(
            raw_manual_moderation_warning_message_location is None
            or raw_manual_moderation_warning_message_location.upper().strip(),
        )
        if not MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_IS_VALID:
            MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE: Final[str] = (
                "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION must be a valid name "
                "of a channel in your group's Discord guild."
            )
            raise ImproperlyConfiguredError(MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE)

        cls._settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = (
            "DM"
            if raw_manual_moderation_warning_message_location is None
            else raw_manual_moderation_warning_message_location.upper().strip()
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
        cls._setup_discord_guild_id()
        cls._setup_group_full_name()
        cls._setup_group_short_name()
        cls._setup_ping_command_easter_egg_probability()
        cls._setup_welcome_messages()
        cls._setup_roles_messages()
        cls._setup_members_list_url()
        cls._setup_members_list_url_session_cookie()
        cls._setup_membership_perks_url()
        cls._setup_purchase_membership_url()
        cls._setup_send_introduction_reminders()
        cls._setup_send_introduction_reminders_interval()
        cls._setup_kick_no_introduction_discord_members()
        cls._setup_kick_no_introduction_discord_members_delay()
        cls._setup_send_get_roles_reminders()
        cls._setup_send_get_roles_reminders_interval()
        cls._setup_statistics_days()
        cls._setup_statistics_roles()
        cls._setup_moderation_document_url()
        cls._setup_manual_moderation_warning_message_location()

        cls._is_env_variables_setup = True


def _settings_class_factory() -> type[Settings]:
    # noinspection PyTypeChecker
    return type(
        "Settings",
        (Settings,),
        {"_is_env_variables_setup": False, "_settings": {}},
    )


settings: Final[Settings] = _settings_class_factory()()


def run_setup() -> None:
    """Execute the setup functions required, before other modules can be run."""
    # noinspection PyProtectedMember
    settings._setup_env_variables()  # noqa: SLF001

    logger.debug("Begin database setup")

    importlib.import_module("db")
    from django.core import management

    management.call_command("migrate")

    logger.debug("Database setup completed")
