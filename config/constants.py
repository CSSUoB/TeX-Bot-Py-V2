"""Constant values that are defined for quick access."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "SendIntroductionRemindersFlagType",
    "LogLevels",
    "PROJECT_ROOT",
    "VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES",
    "MESSAGES_LOCALE_CODES",
    "REQUIRES_RESTART_SETTINGS",
    "DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME",
    "DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY",
    "DEFAULT_DISCORD_LOGGING_LOG_LEVEL",
    "DEFAULT_CONSOLE_LOG_LEVEL",
    "DEFAULT_MEMBERS_LIST_ID_FORMAT",
    "DEFAULT_STATS_COMMAND_LOOKBACK_DAYS",
    "DEFAULT_STATS_COMMAND_DISPLAYED_ROLES",
    "DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION",
    "DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION",
    "DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED",
    "DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY",
    "DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL",
    "DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED",
    "DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY",
    "DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL",
)


from enum import Enum, EnumMeta
from pathlib import Path
from typing import Final, Literal, TypeAlias

from strictyaml import constants as strictyaml_constants

SendIntroductionRemindersFlagType: TypeAlias = Literal["once", "interval", False]


class MetaEnum(EnumMeta):
    def __contains__(cls, item: object) -> bool:  # noqa: N805
        try:
            cls(item)
        except ValueError:
            return False
        return True


class LogLevels(str, Enum, metaclass=MetaEnum):
    """Set of valid string values used for logging log-levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.resolve()

MESSAGES_LOCALE_CODES: Final[frozenset[str]] = frozenset({"en-GB"})


VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES: Final[frozenset[str]] = frozenset(
    ({"once", "interval"} | set(strictyaml_constants.BOOL_VALUES)),
)

REQUIRES_RESTART_SETTINGS: Final[frozenset[str]] = frozenset(
    {
        "discord:bot-token",
        "discord:guild-id",
        "messages-locale-code",
        "reminders:send-introduction-reminders:enabled",
        "reminders:send-introduction-reminders:delay",
        "reminders:send-introduction-reminders:interval",
        "reminders:send-get-roles-reminders:enabled",
        "reminders:send-get-roles-reminders:delay",
        "reminders:send-get-roles-reminders:interval",
    },
)

DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME: Final[str] = "TeX-Bot"


DEFAULT_CONSOLE_LOG_LEVEL: Final[LogLevels] = LogLevels.INFO
DEFAULT_DISCORD_LOGGING_LOG_LEVEL: Final[LogLevels] = LogLevels.WARNING
DEFAULT_MEMBERS_LIST_ID_FORMAT: Final[str] = r"\A\d{6,7}\Z"
DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY: Final[float] = 0.01
DEFAULT_STATS_COMMAND_LOOKBACK_DAYS: Final[float] = 30.0
DEFAULT_STATS_COMMAND_DISPLAYED_ROLES: Final[Sequence[str]] = [
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
]
DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION: Final[str] = "24h"
DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION: Final[str] = "DM"
DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED: Final[SendIntroductionRemindersFlagType] = "once"
DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY: Final[str] = "40h"
DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL: Final[str] = "6h"
DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED: Final[bool] = True
DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY: Final[str] = "40h"
DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL: Final[str] = "6h"
