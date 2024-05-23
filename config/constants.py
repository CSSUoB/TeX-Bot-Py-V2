"""Constant values that are defined for quick access."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "PROJECT_ROOT",
    "VALID_SEND_INTRODUCTION_REMINDERS_VALUES",
    "TRANSLATED_MESSAGES_LOCALE_CODES",
    "DEFAULT_STATISTICS_ROLES",
    "LOG_LEVELS",
    "REQUIRES_RESTART_SETTINGS_KEYS",
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

REQUIRES_RESTART_SETTINGS_KEYS: Final[frozenset[str]] = frozenset(
    {
        "discord-bot-token",
        "discord-guild-id",
        "send-introduction-reminders",
        "send-introduction-reminders-delay",
        "send-introduction-reminders-interval",
        "send-get-roles-reminders",
        "send-get-roles-reminders-delay",
        "send-get-roles-reminders-interval",
    },
)
