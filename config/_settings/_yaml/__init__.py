from typing import TYPE_CHECKING

import strictyaml

from .custom_scalar_validators import (
    BoundedFloatValidator,
    CustomBoolValidator,
    DiscordSnowflakeValidator,
    DiscordWebhookURLValidator,
    LogLevelValidator,
    SendIntroductionRemindersFlagValidator,
    TimeDeltaValidator,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final

    from config.constants import (
        LogLevels,
        SendIntroductionRemindersFlagType,
    )


__all__: "Sequence[str]" = ()

from config.constants import (
    DEFAULT_AUTO_ADD_COMMITTEE_TO_THREADS,
    DEFAULT_CONSOLE_LOG_LEVEL,
    DEFAULT_DISCORD_API_LOGGING_ENABLED,
    DEFAULT_DISCORD_API_LOGGING_FILE_NAME,
    DEFAULT_DISCORD_API_LOGGING_LOG_LEVEL,
    DEFAULT_MSL_AUTO_COOKIE_CHECKING_ENABLED,
    DEFAULT_MSL_AUTO_COOKIE_CHECKING_INTERVAL,
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
    DEFAULT_STRIKE_REPORTED_MESSAGE_DESTINATION_CHANNEL,
)

_DEFAULT_CONSOLE_LOGGING_SETTINGS: "Final[Mapping[str, LogLevels]]" = {
    "log-level": DEFAULT_CONSOLE_LOG_LEVEL,
}
_DEFAULT_DISCORD_API_LOGGING_SETTINGS: "Final[Mapping[str, bool | str]]" = {
    "enabled": DEFAULT_DISCORD_API_LOGGING_ENABLED,
    "log-level": DEFAULT_DISCORD_API_LOGGING_LOG_LEVEL,
    "file-name": DEFAULT_DISCORD_API_LOGGING_FILE_NAME,
}
_DEFAULT_LOGGING_SETTINGS: "Final[Mapping[str, Mapping[str, LogLevels | bool | str]]]" = {
    "console": _DEFAULT_CONSOLE_LOGGING_SETTINGS,
    "discord-api": _DEFAULT_DISCORD_API_LOGGING_SETTINGS,
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
_DEFAULT_COMMANDS_SETTINGS: "Final[Mapping[str, Mapping[str, float] | Mapping[str, float | Sequence[str]] | Mapping[str, str]]]" = {
    "ping": _DEFAULT_PING_COMMAND_SETTINGS,
    "stats": _DEFAULT_STATS_COMMAND_SETTINGS,
    "strike": _DEFAULT_STRIKE_COMMAND_SETTINGS,
}
_DEFAULT_MSL_AUTO_COOKIE_CHECKING_SETTINGS: "Final[Mapping[str, bool | str]]" = {
    "enabled": DEFAULT_MSL_AUTO_COOKIE_CHECKING_ENABLED,
    "interval": DEFAULT_MSL_AUTO_COOKIE_CHECKING_INTERVAL,
}
_DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS: "Final[Mapping[str, SendIntroductionRemindersFlagType | str]]" = {
    "enabled": DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED,
    "delay": DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY,
    "interval": DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL,
}
_DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS: "Final[Mapping[str, bool | str]]" = {
    "enabled": DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED,
    "delay": DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY,
    "interval": DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL,
}
_DEFAULT_REMINDERS_SETTINGS: "Final[Mapping[str, Mapping[str, bool | str] | Mapping[str, SendIntroductionRemindersFlagType | str]]]" = {
    "send-introduction-reminders": _DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS,
    "send-get-roles-reminders": _DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS,
}


SETTINGS_YAML_SCHEMA: "Final[strictyaml.Validator]" = strictyaml.Map({
    strictyaml.Optional("logging", default=_DEFAULT_LOGGING_SETTINGS): strictyaml.Map({
        strictyaml.Optional("console", default=_DEFAULT_CONSOLE_LOGGING_SETTINGS): strictyaml.Map({
            strictyaml.Optional("log-level", default=DEFAULT_CONSOLE_LOG_LEVEL): LogLevelValidator(),
        }),
        strictyaml.Optional("discord-channel", default=_DEFAULT_CONSOLE_LOGGING_SETTINGS): strictyaml.Map({
            "webhook-url": DiscordWebhookURLValidator(),
            strictyaml.Optional("log-level", default=DEFAULT_CONSOLE_LOG_LEVEL): LogLevelValidator(),
        }),
        strictyaml.Optional("discord-api", default=_DEFAULT_DISCORD_API_LOGGING_SETTINGS): strictyaml.Map({
            strictyaml.Optional("enabled", default=DEFAULT_DISCORD_API_LOGGING_ENABLED): CustomBoolValidator(),
            strictyaml.Optional("log-level", default=DEFAULT_DISCORD_API_LOGGING_LOG_LEVEL): LogLevelValidator(),
            strictyaml.Optional("file-name", default=DEFAULT_DISCORD_API_LOGGING_FILE_NAME): strictyaml.Str(),
        }),
    }),
    "discord": strictyaml.Map({
        "bot-token": strictyaml.Regex(r"\A(?!.*__.*)(?!.*--.*)(?:([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38}))\Z"),
        "main-guild-id": DiscordSnowflakeValidator(),
    }),
    "community-group": strictyaml.Map({
        strictyaml.Optional("full-name"): strictyaml.Regex(r"\A.{1,50}\Z"),
        strictyaml.Optional("short-name"): strictyaml.Regex(r"\A(?!.*['&!?:,.#%\"-]['&!?:,.#%\"-].*)(?:[A-Za-z0-9'&!?:,.#%\"-]+)\Z",),
        strictyaml.Optional("membership-dependent-roles"): strictyaml.UniqueSeq(strictyaml.Str()),
        "links": strictyaml.Map({
            strictyaml.Optional("purchase-membership"): strictyaml.Url(),
            strictyaml.Optional("membership-perks"): strictyaml.Url(),
            strictyaml.Optional("moderation-policy"): strictyaml.Url(),
            strictyaml.Optional("custom-discord-invite-link"): strictyaml.Url(),
        }),
        "msl": strictyaml.Map({
            strictyaml.Optional("organisation-id"): strictyaml.Regex(r"\A\d{4,5}\Z"),
            strictyaml.Optional("auth-cookie"): strictyaml.Regex(r"\A[\w-]{512,1024}\Z"),
            strictyaml.Optional("auto-cookie-checking", default=_DEFAULT_MSL_AUTO_COOKIE_CHECKING_SETTINGS): strictyaml.Map({
                strictyaml.Optional("enabled", default=DEFAULT_MSL_AUTO_COOKIE_CHECKING_ENABLED): CustomBoolValidator(),
                strictyaml.Optional("interval", default=DEFAULT_MSL_AUTO_COOKIE_CHECKING_INTERVAL): TimeDeltaValidator(minutes=True, hours=True, days=True),
            }),
        }),
    }),
    strictyaml.Optional("commands", default=_DEFAULT_COMMANDS_SETTINGS): strictyaml.Map({
        strictyaml.Optional("ping", default=_DEFAULT_PING_COMMAND_SETTINGS): strictyaml.Map({
            strictyaml.Optional("easter-egg-probability", default=DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY): BoundedFloatValidator(0, 1),
        }),
        strictyaml.Optional("stats", default=_DEFAULT_STATS_COMMAND_SETTINGS): strictyaml.Map({
            strictyaml.Optional("lookback-days", default=DEFAULT_STATS_COMMAND_LOOKBACK_DAYS): BoundedFloatValidator(5, 1826),
            strictyaml.Optional("displayed-roles", default=DEFAULT_STATS_COMMAND_DISPLAYED_ROLES): strictyaml.UniqueSeq(strictyaml.Str()),
        }),
        strictyaml.Optional("strike", default=_DEFAULT_STRIKE_COMMAND_SETTINGS): strictyaml.Map({
            strictyaml.Optional("performed-manually-warning-location", default=DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION): strictyaml.Str(),
            strictyaml.Optional("timeout-duration", default=DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION): TimeDeltaValidator(minutes=True, hours=True, days=True),
            strictyaml.Optional("reported-message-destination-channel", default=DEFAULT_STRIKE_REPORTED_MESSAGE_DESTINATION_CHANNEL): strictyaml.Str(),
        }),
    }),
    strictyaml.Optional("reminders", default=_DEFAULT_REMINDERS_SETTINGS): strictyaml.Map({
        strictyaml.Optional("send-introduction-reminders", default=_DEFAULT_SEND_INTRODUCTION_REMINDERS_SETTINGS): strictyaml.Map({
            strictyaml.Optional("enabled", default=DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED): SendIntroductionRemindersFlagValidator(),
            strictyaml.Optional("delay", default=DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY): TimeDeltaValidator(minutes=True, hours=True, days=True),
            strictyaml.Optional("interval", default=DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL): TimeDeltaValidator(minutes=True, hours=True, days=True),
        }),
        strictyaml.Optional("send-get-roles-reminders", default=_DEFAULT_SEND_GET_ROLES_REMINDERS_SETTINGS): strictyaml.Map({
            strictyaml.Optional("enabled", default=DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED): CustomBoolValidator(),
            strictyaml.Optional("delay", default=DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY): TimeDeltaValidator(minutes=True, hours=True, days=True),
            strictyaml.Optional("interval", default=DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL): TimeDeltaValidator(minutes=True, hours=True, days=True),
        }),
    }),
    strictyaml.Optional("auto-add-committee-to-threads", default=DEFAULT_AUTO_ADD_COMMITTEE_TO_THREADS): CustomBoolValidator(),
})
