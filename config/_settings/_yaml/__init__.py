
from typing import TYPE_CHECKING

import strictyaml

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final


__all__: "Sequence[str]" = ()

from config.constants import (
    DEFAULT_CHECK_IF_CONFIG_CHANGED_INTERVAL,
    DEFAULT_CONSOLE_LOG_LEVEL,
    DEFAULT_DISCORD_LOGGING_LOG_LEVEL,
    DEFAULT_MEMBERS_LIST_ID_FORMAT,
    DEFAULT_MESSAGE_LOCALE_CODE,
    DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY,
    DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY,
    DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED,
    DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL,
    DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY,
    DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED,
    DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL,
    DEFAULT_STATS_COMMAND_DISPLAYED_ROLES,
    DEFAULT_STATS_COMMAND_LOOKBACK_DAYS,
    DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION,
    DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION,
    MESSAGES_LOCALE_CODES,
    LogLevels,
    SendIntroductionRemindersFlagType,
)

_DEFAULT_CONSOLE_LOGGING_SETTINGS: "Final[Mapping[str, LogLevels]]" = {
    "log-level": DEFAULT_CONSOLE_LOG_LEVEL,
}
_DEFAULT_LOGGING_SETTINGS: "Final[Mapping[str, Mapping[str, LogLevels]]]" = {
    "console": _DEFAULT_CONSOLE_LOGGING_SETTINGS,
}
_DEFAULT_PING_COMMAND_SETTINGS: "Final[Mapping[str, float]]" = {
    "easter-egg-probability": DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY,
}
_DEFAULT_STATS_COMMAND_SETTINGS: "Final[Mapping[str, float | Sequence[str]]]" = {
    "lookback-days": DEFAULT_STATS_COMMAND_LOOKBACK_DAYS,
    "displayed-roles": DEFAULT_STATS_COMMAND_DISPLAYED_ROLES,
}
_DEFAULT_STRIKE_COMMAND_SETTINGS: "Final[Mapping[str, str]]" = {
    "timeout-duration": DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION,
    "performed-manually-warning-location": DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION,
}
_DEFAULT_COMMANDS_SETTINGS: "Final[Mapping[str, Mapping[str, float] | Mapping[str, float | Sequence[str]] | Mapping[str, str]]]" = {  # noqa: E501
    "ping": _DEFAULT_PING_COMMAND_SETTINGS,
    "stats": _DEFAULT_STATS_COMMAND_SETTINGS,
    "strike": _DEFAULT_STRIKE_COMMAND_SETTINGS,
}
_DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS: "Final[Mapping[str, SendIntroductionRemindersFlagType | str]]" = {  # noqa: E501
    "enabled": DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED,
    "delay": DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY,
    "interval": DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL,
}
_DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS: "Final[Mapping[str, bool | str]]" = {
    "enabled": DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED,
    "delay": DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY,
    "interval": DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL,
}
_DEFAULT_REMINDERS_SETTINGS: "Final[Mapping[str, Mapping[str, bool | str] | Mapping[str, SendIntroductionRemindersFlagType | str]]]" = {  # noqa: E501
    "send-introduction-reminders": _DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS,
    "send-get-roles-reminders": _DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS,
}


SETTINGS_YAML_SCHEMA: "Final[strictyaml.Validator]" = strictyaml.Map(
    
)





