"""Constant values that are defined for quick access."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "PROJECT_ROOT",
    "VALID_SEND_INTRODUCTION_REMINDERS_VALUES",
    "TRANSLATED_MESSAGES_LOCALE_CODES",
    "DEFAULT_STATISTICS_ROLES",
    "LOG_LEVELS",
    "REQUIRES_RESTART_SETTINGS",
    "DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME",
)


from pathlib import Path
from typing import Final

from strictyaml import constants as strictyaml_constants

PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.resolve()

VALID_SEND_INTRODUCTION_REMINDERS_VALUES: Final[frozenset[str]] = frozenset(
    ({"once", "interval"} | set(strictyaml_constants.BOOL_VALUES)),
)

TRANSLATED_MESSAGES_LOCALE_CODES: Final[frozenset[str]] = frozenset({"en-GB"})

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

LOG_LEVELS: Final[Sequence[str]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)

REQUIRES_RESTART_SETTINGS: Final[frozenset[str]] = frozenset(
    {
        "discord:bot-token",
        "discord:guild-id",
        "reminders:send-introduction-reminders:enable",
        "reminders:send-introduction-reminders:delay",
        "reminders:send-introduction-reminders:interval",
        "reminders:send-get-roles-reminders:enable",
        "reminders:send-get-roles-reminders:delay",
        "reminders:send-get-roles-reminders:interval",
    },
)

DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME: Final[str] = "TeX-Bot"
