from collections.abc import Sequence

__all__: Sequence[str] = (
    "DiscordWebhookURLValidator",
    "LogLevelValidator",
    "DiscordSnowflakeValidator",
    "ProbabilityValidator",
    "SendIntroductionRemindersFlagValidator",
    "SETTINGS_YAML_SCHEMA",
    "load_yaml",
)

from collections.abc import Mapping
from typing import Final

import strictyaml
from strictyaml import YAML

from ..constants import DEFAULT_STATISTICS_ROLES, TRANSLATED_MESSAGES_LOCALE_CODES
from .custom_validators import (
    DiscordWebhookURLValidator,
    LogLevelValidator,
    DiscordSnowflakeValidator,
    ProbabilityValidator,
    SendIntroductionRemindersFlagValidator,
    SendIntroductionRemindersFlagType,
    LogLevelType,
)
from .custom_schema_utils import SlugKeyMap


_DEFAULT_CONSOLE_LOG_LEVEL: Final[LogLevelType] = "INFO"
_DEFAULT_CONSOLE_LOGGING_SETTINGS: Final[Mapping[str, str]] = {
    "log-level": _DEFAULT_CONSOLE_LOG_LEVEL,
}
_DEFAULT_LOGGING_SETTINGS: Final[Mapping[str, Mapping[str, str]]] = {
    "console": _DEFAULT_CONSOLE_LOGGING_SETTINGS,
}
_DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY: Final[float] = 0.01
_DEFAULT_PING_COMMAND_SETTINGS: Final[Mapping[str, float]] = {
    "easter-egg-probability": _DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY,
}
_DEFAULT_STATS_COMMAND_LOOKBACK_DAYS: Final[float] = 30.0
_DEFAULT_STATS_COMMAND_DISPLAYED_ROLES: Final[Sequence[str]] = list(DEFAULT_STATISTICS_ROLES)
_DEFAULT_STATS_COMMAND_SETTINGS: Final[Mapping[str, float | Sequence[str]]] = {
    "lookback-days": _DEFAULT_STATS_COMMAND_LOOKBACK_DAYS,
    "displayed-roles": _DEFAULT_STATS_COMMAND_DISPLAYED_ROLES,
}
_DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION: Final[str] = "24h"
_DEFAULT_STRIKE_COMMAND_MANUAL_USE_WARNING_LOCATION: Final[str] = "DM"
_DEFAULT_STRIKE_COMMAND_SETTINGS: Final[Mapping[str, str]] = {
    "timeout-duration": _DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION,
    "manual-use-warning-location": _DEFAULT_STRIKE_COMMAND_MANUAL_USE_WARNING_LOCATION,
}
_DEFAULT_COMMANDS_SETTINGS: Final[Mapping[str, Mapping[str, float]]] = {
    "ping": _DEFAULT_PING_COMMAND_SETTINGS,
    "stats": _DEFAULT_STATS_COMMAND_SETTINGS,
    "strike": _DEFAULT_STRIKE_COMMAND_SETTINGS,
}
_DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY: Final[str] = "40h"
_DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL: Final[str] = "6h"
_DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS: Final[Mapping[str, SendIntroductionRemindersFlagType | str]] = {
    "enable": "once",
    "delay": _DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY,
    "interval": _DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL,
}
_DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY: Final[str] = "40h"
_DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL: Final[str] = "6h"
_DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS: Final[Mapping[str, bool | str]] = {
    "enable": True,
    "delay": _DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY,
    "interval": _DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL,
}
_DEFAULT_REMINDERS_SETTINGS: Final[Mapping[str, Mapping[str, bool | str] | Mapping[str, SendIntroductionRemindersFlagType | str]]] = {  # noqa: E501
    "send-introduction-reminders": _DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS,
    "send-get-roles-reminders": _DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS,
}

SETTINGS_YAML_SCHEMA: Final[strictyaml.Validator] = SlugKeyMap(  # type: ignore[no-any-unimported]
    {
        strictyaml.Optional("logging", default=_DEFAULT_LOGGING_SETTINGS): SlugKeyMap(
            {
                strictyaml.Optional("console", default=_DEFAULT_CONSOLE_LOGGING_SETTINGS): SlugKeyMap(  # noqa: E501
                    {
                        strictyaml.Optional("log-level", default=_DEFAULT_CONSOLE_LOG_LEVEL): (
                            LogLevelValidator()
                        ),
                    },
                ),
                strictyaml.Optional("discord-channel"): SlugKeyMap(
                    {
                        "webhook-url": DiscordWebhookURLValidator(),
                        strictyaml.Optional("log-level", default="WARNING"): (
                            LogLevelValidator()
                        ),
                    },
                ),
            },
        ),
        "discord": SlugKeyMap(
            {
                "bot-token": strictyaml.Regex(
                    r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z",
                ),
                "main-guild-id": DiscordSnowflakeValidator(),
            },
        ),
        "community-group": SlugKeyMap(
            {
                strictyaml.Optional("full-name"): strictyaml.Regex(
                    r"\A[A-Za-z0-9 '&!?:,.#%\"-]+\Z",
                ),
                strictyaml.Optional("short-name"): strictyaml.Regex(
                    r"\A[A-Za-z0-9'&!?:,.#%\"-]+\Z",
                ),
                strictyaml.Optional("links"): SlugKeyMap(
                    {
                        strictyaml.Optional("purchase-membership"): strictyaml.Url(),
                        strictyaml.Optional("membership-perks"): strictyaml.Url(),
                        strictyaml.Optional("moderation-document"): strictyaml.Url(),
                    }
                ),
                "members-list": SlugKeyMap(
                    {
                        "url": strictyaml.Url(),
                        "auth-session-cookie": strictyaml.Str(),
                        strictyaml.Optional("id-format", default=r"\A\d{6,7}\Z"): (
                            strictyaml.Str()
                        ),
                    },
                ),
            },
        ),
        strictyaml.Optional("commands", default=_DEFAULT_COMMANDS_SETTINGS): SlugKeyMap(
            {
                strictyaml.Optional("ping", default=_DEFAULT_PING_COMMAND_SETTINGS): SlugKeyMap(  # noqa: E501
                    {
                        strictyaml.Optional("easter-egg-probability", default=_DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY): (  # noqa: E501
                            ProbabilityValidator()
                        ),
                    },
                ),
                strictyaml.Optional("stats", default=_DEFAULT_STATS_COMMAND_SETTINGS): (
                    SlugKeyMap(
                        {
                            strictyaml.Optional("lookback-days", default=_DEFAULT_STATS_COMMAND_LOOKBACK_DAYS): (  # noqa: E501
                                strictyaml.Float()
                            ),
                            strictyaml.Optional("displayed-roles", default=_DEFAULT_STATS_COMMAND_DISPLAYED_ROLES): (  # noqa: E501
                                strictyaml.UniqueSeq(strictyaml.Str())
                            ),
                        },
                    )
                ),
                strictyaml.Optional("strike", default=_DEFAULT_STRIKE_COMMAND_SETTINGS): (
                    SlugKeyMap(
                        {
                            strictyaml.Optional("timeout-duration", default=_DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION): (  # noqa: E501
                                strictyaml.Regex(
                                    r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
                                )
                            ),
                            strictyaml.Optional("manual-use-warning-location", default=_DEFAULT_STRIKE_COMMAND_MANUAL_USE_WARNING_LOCATION): (  # noqa: E501
                                strictyaml.Str()
                            ),
                        },
                    )
                ),
            },
        ),
        strictyaml.Optional("messages-language", default="en-GB"): strictyaml.Enum(
            TRANSLATED_MESSAGES_LOCALE_CODES,
        ),
        strictyaml.Optional("reminders", default=_DEFAULT_REMINDERS_SETTINGS): SlugKeyMap(
            {
                strictyaml.Optional("send-introduction-reminders", default=_DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS): SlugKeyMap(  # noqa: E501
                    {
                        "enable": SendIntroductionRemindersFlagValidator(),
                        strictyaml.Optional("delay", default=_DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY): (  # noqa: E501
                            strictyaml.Regex(
                                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
                            )
                        ),
                        strictyaml.Optional("interval", default=_DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL): (  # noqa: E501
                            strictyaml.Regex(
                                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
                            )
                        ),
                    },
                ),
                strictyaml.Optional("send-get-roles-reminders", default=_DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS): SlugKeyMap(  # noqa: E501
                    {
                        "enable": strictyaml.Bool(),
                        strictyaml.Optional("delay", default=_DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY): (  # noqa: E501
                            strictyaml.Regex(
                                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
                            )
                        ),
                        strictyaml.Optional("interval", default=_DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL): (  # noqa: E501
                            strictyaml.Regex(
                                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
                            )
                        ),
                    },
                ),
            },
        ),
    },
)


def load_yaml(raw_yaml: str) -> YAML:
    parsed_yaml: YAML = strictyaml.load(raw_yaml, SETTINGS_YAML_SCHEMA)  # type: ignore[no-any-unimported]

    # noinspection SpellCheckingInspection
    if "guildofstudents" in parsed_yaml["community-group"]["members-list"]["url"]:
        parsed_yaml["community-group"]["members-list"]["auth-session-cookie"].revalidate(
            strictyaml.Regex(r"\A[A-Fa-f\d]{128,256}\Z"),
        )

    return parsed_yaml
