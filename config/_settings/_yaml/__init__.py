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

from config.constants import (
    DEFAULT_CONSOLE_LOG_LEVEL,
    DEFAULT_DISCORD_LOGGING_LOG_LEVEL,
    DEFAULT_MEMBERS_LIST_ID_FORMAT,
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

from .custom_map_validator import SlugKeyMap
from .custom_scalar_validators import (
    DiscordSnowflakeValidator,
    DiscordWebhookURLValidator,
    LogLevelValidator,
    ProbabilityValidator,
    RegexMatcher,
    SendIntroductionRemindersFlagValidator,
    TimeDeltaValidator,
)

_DEFAULT_CONSOLE_LOGGING_SETTINGS: Final[Mapping[str, LogLevels]] = {
    "log-level": DEFAULT_CONSOLE_LOG_LEVEL,
}
_DEFAULT_LOGGING_SETTINGS: Final[Mapping[str, Mapping[str, LogLevels]]] = {
    "console": _DEFAULT_CONSOLE_LOGGING_SETTINGS,
}
_DEFAULT_PING_COMMAND_SETTINGS: Final[Mapping[str, float]] = {
    "easter-egg-probability": DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY,
}
_DEFAULT_STATS_COMMAND_SETTINGS: Final[Mapping[str, float | Sequence[str]]] = {
    "lookback-days": DEFAULT_STATS_COMMAND_LOOKBACK_DAYS,
    "displayed-roles": DEFAULT_STATS_COMMAND_DISPLAYED_ROLES,
}
_DEFAULT_STRIKE_COMMAND_SETTINGS: Final[Mapping[str, str]] = {
    "timeout-duration": DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION,
    "performed-manually-warning-location": DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION,
}
_DEFAULT_COMMANDS_SETTINGS: Final[Mapping[str, Mapping[str, float] | Mapping[str, float | Sequence[str]] | Mapping[str, str]]] = {  # noqa: E501
    "ping": _DEFAULT_PING_COMMAND_SETTINGS,
    "stats": _DEFAULT_STATS_COMMAND_SETTINGS,
    "strike": _DEFAULT_STRIKE_COMMAND_SETTINGS,
}
_DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS: Final[Mapping[str, SendIntroductionRemindersFlagType | str]] = {  # noqa: E501
    "enabled": DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED,
    "delay": DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY,
    "interval": DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL,
}
_DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS: Final[Mapping[str, bool | str]] = {
    "enabled": DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED,
    "delay": DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY,
    "interval": DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL,
}
_DEFAULT_REMINDERS_SETTINGS: Final[Mapping[str, Mapping[str, bool | str] | Mapping[str, SendIntroductionRemindersFlagType | str]]] = {  # noqa: E501
    "send-introduction-reminders": _DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS,
    "send-get-roles-reminders": _DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS,
}

SETTINGS_YAML_SCHEMA: Final[strictyaml.Validator] = SlugKeyMap(  # type: ignore[no-any-unimported]
    {
        strictyaml.Optional("logging", default=_DEFAULT_LOGGING_SETTINGS): SlugKeyMap(
            {
                strictyaml.Optional("console", default=_DEFAULT_CONSOLE_LOGGING_SETTINGS): (
                    SlugKeyMap(
                        {
                            strictyaml.Optional("log-level", default=DEFAULT_CONSOLE_LOG_LEVEL): (  # noqa: E501
                                LogLevelValidator()
                            ),
                        },
                    )
                ),
                strictyaml.Optional("discord-channel"): SlugKeyMap(
                    {
                        "webhook-url": DiscordWebhookURLValidator(),
                        strictyaml.Optional("log-level", default=DEFAULT_DISCORD_LOGGING_LOG_LEVEL): (  # noqa: E501
                            LogLevelValidator()
                        ),
                    },
                ),
            },
        ),
        "discord": SlugKeyMap(
            {
                "bot-token": strictyaml.Regex(
                    r"\A(?!.*__.*)(?!.*--.*)(?:([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38}))\Z",
                ),
                "main-guild-id": DiscordSnowflakeValidator(),
            },
        ),
        "community-group": SlugKeyMap(
            {
                strictyaml.Optional("full-name"): strictyaml.Regex(
                    (
                        r"\A(?!.*['&!?:,.#%\"-]['&!?:,.#%\"-].*)(?!.*  .*)"
                        r"(?:[A-Za-z0-9 '&!?:,.#%\"-]+)\Z"
                    ),
                ),
                strictyaml.Optional("short-name"): strictyaml.Regex(
                    r"\A(?!.*['&!?:,.#%\"-]['&!?:,.#%\"-].*)(?:[A-Za-z0-9'&!?:,.#%\"-]+)\Z",
                ),
                "links": SlugKeyMap(
                    {
                        strictyaml.Optional("purchase-membership"): strictyaml.Url(),
                        strictyaml.Optional("membership-perks"): strictyaml.Url(),
                        "moderation-document": strictyaml.Url(),
                    },
                ),
                "members-list": SlugKeyMap(
                    {
                        "url": strictyaml.Url(),
                        "auth-session-cookie": strictyaml.Str(),
                        strictyaml.Optional("id-format", default=DEFAULT_MEMBERS_LIST_ID_FORMAT): (  # noqa: E501
                            RegexMatcher()
                        ),
                    },
                ),
            },
        ),
        strictyaml.Optional("commands", default=_DEFAULT_COMMANDS_SETTINGS): SlugKeyMap(
            {
                strictyaml.Optional("ping", default=_DEFAULT_PING_COMMAND_SETTINGS): SlugKeyMap(  # noqa: E501
                    {
                        strictyaml.Optional("easter-egg-probability", default=DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY): (  # noqa: E501
                            ProbabilityValidator()
                        ),
                    },
                ),
                strictyaml.Optional("stats", default=_DEFAULT_STATS_COMMAND_SETTINGS): (
                    SlugKeyMap(
                        {
                            strictyaml.Optional("lookback-days", default=DEFAULT_STATS_COMMAND_LOOKBACK_DAYS): (  # noqa: E501
                                strictyaml.Float()
                            ),
                            strictyaml.Optional("displayed-roles", default=DEFAULT_STATS_COMMAND_DISPLAYED_ROLES): (  # noqa: E501
                                strictyaml.UniqueSeq(strictyaml.Str())
                            ),
                        },
                    )
                ),
                strictyaml.Optional("strike", default=_DEFAULT_STRIKE_COMMAND_SETTINGS): (
                    SlugKeyMap(
                        {
                            strictyaml.Optional("timeout-duration", default=DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION): (  # noqa: E501
                                TimeDeltaValidator(
                                    minutes=True,
                                    hours=True,
                                    days=True,
                                    weeks=True,
                                )
                            ),
                            strictyaml.Optional("performed-manually-warning-location", default=DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION): (  # noqa: E501
                                strictyaml.Str()
                            ),
                        },
                    )
                ),
            },
        ),
        strictyaml.Optional("messages-locale", default="en-GB"): strictyaml.Enum(
            MESSAGES_LOCALE_CODES,
        ),
        strictyaml.Optional("reminders", default=_DEFAULT_REMINDERS_SETTINGS): SlugKeyMap(
            {
                strictyaml.Optional("send-introduction-reminders", default=_DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS): SlugKeyMap(  # noqa: E501
                    {
                        "enabled": SendIntroductionRemindersFlagValidator(),
                        strictyaml.Optional("delay", default=DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY): (  # noqa: E501
                            TimeDeltaValidator(minutes=True, hours=True, days=True, weeks=True)
                        ),
                        strictyaml.Optional("interval", default=DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL): (  # noqa: E501
                            TimeDeltaValidator(minutes=True, hours=True)
                        ),
                    },
                ),
                strictyaml.Optional("send-get-roles-reminders", default=_DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS): SlugKeyMap(  # noqa: E501
                    {
                        "enabled": strictyaml.Bool(),
                        strictyaml.Optional("delay", default=DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY): (  # noqa: E501
                            TimeDeltaValidator(minutes=True, hours=True, days=True, weeks=True)
                        ),
                        strictyaml.Optional("interval", default=DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL): (  # noqa: E501
                            TimeDeltaValidator(minutes=True, hours=True)
                        ),
                    },
                ),
            },
        ),
    },
)


def load_yaml(raw_yaml: str, file_name: str = "tex-bot-deployment.yaml") -> YAML:  # type: ignore[no-any-unimported]
    parsed_yaml: YAML = strictyaml.load(raw_yaml, SETTINGS_YAML_SCHEMA, label=file_name)  # type: ignore[no-any-unimported]

    # noinspection SpellCheckingInspection
    if "guildofstudents" in parsed_yaml["community-group"]["members-list"]["url"]:
        parsed_yaml["community-group"]["members-list"]["auth-session-cookie"].revalidate(
            strictyaml.Regex(r"\A[A-Fa-f\d]{128,256}\Z"),
        )

    return parsed_yaml
