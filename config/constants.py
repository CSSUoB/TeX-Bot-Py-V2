"""Constant values that are defined for quick access."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "SendIntroductionRemindersFlagType",
    "LogLevels",
    "ConfigSettingHelp",
    "PROJECT_ROOT",
    "VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES",
    "MESSAGES_LOCALE_CODES",
    "DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME",
    "DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY",
    "DEFAULT_DISCORD_LOGGING_LOG_LEVEL",
    "DEFAULT_CONSOLE_LOG_LEVEL",
    "DEFAULT_MEMBERS_LIST_ID_FORMAT",
    "DEFAULT_STATS_COMMAND_LOOKBACK_DAYS",
    "DEFAULT_STATS_COMMAND_DISPLAYED_ROLES",
    "DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION",
    "DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION",
    "DEFAULT_MESSAGE_LOCALE_CODE",
    "DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED",
    "DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY",
    "DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL",
    "DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED",
    "DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY",
    "DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL",
    "CONFIG_SETTINGS_HELPS",
)


from collections.abc import Iterable, Mapping
from enum import Enum, EnumMeta
from pathlib import Path
from typing import Final, Literal, NamedTuple, TypeAlias

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


class ConfigSettingHelp(NamedTuple):
    """Container to hold help information about a single configuration setting."""

    description: str
    value_type_message: str | None
    requires_restart_after_changed: bool
    required: bool = True
    default: str | None = None


def _selectable_required_format_message(options: Iterable[str]) -> str:
    return f"Must be one of: `{"`, `".join(options)}`."


def _custom_required_format_message(type_value: str, info_link: str | None = None) -> str:
    return (
        f"Must be a valid {
            type_value.lower().replace("discord", "Discord").replace(
                "id",
                "ID",
            ).replace("url", "URL").strip(".")
        }{f" (see <{info_link}>)" if info_link else ""}."
    )


PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.resolve()

MESSAGES_LOCALE_CODES: Final[frozenset[str]] = frozenset({"en-GB"})


VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES: Final[frozenset[str]] = frozenset(
    ({"once", "interval"} | set(strictyaml_constants.BOOL_VALUES)),
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
DEFAULT_MESSAGE_LOCALE_CODE: Final[str] = "en-GB"
DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED: Final[SendIntroductionRemindersFlagType] = "once"
DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY: Final[str] = "40h"
DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL: Final[str] = "6h"
DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED: Final[bool] = True
DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY: Final[str] = "40h"
DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL: Final[str] = "6h"

CONFIG_SETTINGS_HELPS: Mapping[str, ConfigSettingHelp] = {
    "logging:console:log-level": ConfigSettingHelp(
        description=(
            "The minimum level that logs must meet in order to be logged "
            "to the console output stream."
        ),
        value_type_message=_selectable_required_format_message(LogLevels),
        requires_restart_after_changed=False,
        required=False,
        default=DEFAULT_CONSOLE_LOG_LEVEL,
    ),
    "logging:discord-channel:log-level": ConfigSettingHelp(
        description=(
            "The minimum level that logs must meet in order to be logged "
            "to the Discord log channel."
        ),
        value_type_message=_selectable_required_format_message(LogLevels),
        requires_restart_after_changed=False,
        required=False,
        default=DEFAULT_DISCORD_LOGGING_LOG_LEVEL,
    ),
    "logging:discord-channel:webhook-url": ConfigSettingHelp(
        description=(
            "The webhook URL of the Discord text channel where error logs should be sent.\n"
            "Error logs will always be sent to the console, "
            "this setting allows them to also be sent to a Discord log channel."
        ),
        value_type_message=_custom_required_format_message(
            "Discord webhook URL",
            "https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks",
        ),
        requires_restart_after_changed=False,
        required=False,
        default=None,
    ),
    "discord:bot-token": ConfigSettingHelp(
        description=(
            "The Discord token for the bot you created "
            "(available on your bot page in the developer portal: <https://discord.com/developers/applications>)."
        ),
        value_type_message=_custom_required_format_message(
            "Discord bot token",
            "https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts",
        ),
        requires_restart_after_changed=True,
        required=True,
        default=None,
    ),
    "discord:main-guild-id": ConfigSettingHelp(
        description="The ID of your community group's main Discord guild.",
        value_type_message=_custom_required_format_message(
            "Discord guild ID",
            "https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id",
        ),
        requires_restart_after_changed=True,
        required=True,
        default=None,
    ),
    "community-group:full-name": ConfigSettingHelp(
        description=(
            "The full name of your community group, do **NOT** use an abbreviation.\n"
            "This is substituted into many error/welcome messages "
            "sent into your Discord guild, by **`@TeX-Bot`**.\n"
            "If this is not set the group-full-name will be retrieved "
            "from the name of your group's Discord guild."
        ),
        requires_restart_after_changed=False,
        value_type_message=None,
        required=False,
        default=None,
    ),
    "community-group:short-name": ConfigSettingHelp(
        description=(
            "The short colloquial name of your community group, "
            "it is recommended that you set this to be an abbreviation of your group's name.\n"
            "If this is not set the group-short-name will be determined "
            "from your group's full name."
        ),
        requires_restart_after_changed=False,
        value_type_message=None,
        required=False,
        default=None,
    ),
    "community-group:links:purchase-membership": ConfigSettingHelp(
        description=(
            "The link to the page where guests can purchase a full membership "
            "to join your community group."
        ),
        requires_restart_after_changed=False,
        value_type_message=_custom_required_format_message("URL"),
        required=False,
        default=None,
    ),
    "community-group:links:membership-perks": ConfigSettingHelp(
        description=(
            "The link to the page where guests can find out information "
            "about the perks that they will receive "
            "once they purchase a membership to your community group."
        ),
        requires_restart_after_changed=False,
        value_type_message=_custom_required_format_message("URL"),
        required=False,
        default=None,
    ),
    "community-group:links:moderation-document": ConfigSettingHelp(
        description="The link to your group's Discord guild moderation document.",
        value_type_message=_custom_required_format_message("URL"),
        requires_restart_after_changed=False,
        required=True,
        default=None,
    ),
    "community-group:members-list:url": ConfigSettingHelp(
        description=(
            "The URL to retrieve the list of IDs of people that have purchased a membership "
            "to your community group.\n"
            "Ensure that all members are visible without pagination, "
            "(for example, "
            "if your members-list is found on the UoB Guild of Students website, "
            "ensure the URL includes the \"sort by groups\" option)."
        ),
        requires_restart_after_changed=False,
        value_type_message=_custom_required_format_message("URL"),
        required=True,
        default=None,
    ),
    "community-group:members-list:auth-session-cookie": ConfigSettingHelp(
        description=(
            "The members-list authentication session cookie.\n"
            "If your group's members-list is stored at a URL that requires authentication, "
            "this session cookie should authenticate **`@TeX-Bot`** "
            "to view your group's members-list, "
            "as if it were logged in to the website as a Committee member.\n"
            "If your members-list is found on the UoB Guild of Students website, "
            "this can be extracted from your web-browser: "
            "after manually logging in to view your members-list, "
            "it will probably be listed as a cookie named `.ASPXAUTH`."
        ),
        requires_restart_after_changed=False,
        value_type_message=None,
        required=True,
        default=None,
    ),
    "community-group:members-list:id-format": ConfigSettingHelp(
        description=(
            "The format that IDs are stored in within your members-list.\n"
            "Remember to double escape `\\` characters where necessary."
        ),
        value_type_message=_custom_required_format_message(
            "regex matcher string",
        ),
        requires_restart_after_changed=False,
        required=False,
        default=DEFAULT_MEMBERS_LIST_ID_FORMAT,
    ),
    "commands:ping:easter-egg-probability": ConfigSettingHelp(
        description=(
            "The probability that the more rare ping command response will be sent "
            "instead of the normal one."
        ),
        value_type_message=_custom_required_format_message(
            "float, inclusively between 1 & 0",
        ),
        requires_restart_after_changed=False,
        required=False,
        default=str(DEFAULT_PING_COMMAND_EASTER_EGG_PROBABILITY),
    ),
    "commands:stats:lookback-days": ConfigSettingHelp(
        description=(
            "The number of days to look over messages sent, to generate statistics data."
        ),
        value_type_message=_custom_required_format_message(
            "float representing the number of days to look back through",
        ),
        requires_restart_after_changed=False,
        required=False,
        default=str(DEFAULT_STATS_COMMAND_LOOKBACK_DAYS),
    ),
    "commands:stats:displayed-roles": ConfigSettingHelp(
        description=(
            "The names of the roles to gather statistics about, "
            "to display in bar chart graphs."
        ),
        value_type_message=_custom_required_format_message(
            "comma seperated list of strings of role names",
        ),
        requires_restart_after_changed=False,
        required=False,
        default=",".join(DEFAULT_STATS_COMMAND_DISPLAYED_ROLES),
    ),
    "commands:strike:timeout-duration": ConfigSettingHelp(
        description=(
            "The amount of time to timeout a user when using the **`/strike`** command."
        ),
        value_type_message=_custom_required_format_message(
            (
                "string of the seconds, minutes, hours, days or weeks "
                "to timeout a user (format: `<seconds>s<minutes>m<hours>h<days>d<weeks>w`)"
            ),
        ),
        requires_restart_after_changed=False,
        required=False,
        default=DEFAULT_STRIKE_COMMAND_TIMEOUT_DURATION,
    ),
    "commands:strike:performed-manually-warning-location": ConfigSettingHelp(
        description=(
            "The name of the channel, that warning messages will be sent to "
            "when a committee-member manually applies a moderation action "
            "(instead of using the `/strike` command).\n"
            "This can be the name of **ANY** Discord channel "
            "(so the offending person *will* be able to see these messages "
            "if a public channel is chosen)."
        ),
        value_type_message=_custom_required_format_message(
            (
                "name of a Discord channel in your group's Discord guild, "
                "or the value `DM` "
                "(which indicates that the messages will be sent "
                "in the committee-member's DMs)"
            ),
        ),
        requires_restart_after_changed=False,
        required=False,
        default=DEFAULT_STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION,
    ),
    "messages-locale-code": ConfigSettingHelp(
        description=(
            "The locale code used to select the language response messages will be given in."
        ),
        value_type_message=_selectable_required_format_message(
            MESSAGES_LOCALE_CODES,
        ),
        requires_restart_after_changed=False,
        required=False,
        default=DEFAULT_MESSAGE_LOCALE_CODE,
    ),
    "reminders:send-introduction-reminders:enabled": ConfigSettingHelp(
        description=(
            "Whether introduction reminders will be sent to Discord members "
            "that are not inducted, "
            "saying that they need to send an introduction to be allowed access."
        ),
        value_type_message=_selectable_required_format_message(
            (
                str(flag_value).lower()
                for flag_value
                in getattr(SendIntroductionRemindersFlagType, "__args__")  # noqa: B009
            ),
        ),
        requires_restart_after_changed=True,
        required=False,
        default=str(DEFAULT_SEND_INTRODUCTION_REMINDERS_ENABLED).lower(),
    ),
    "reminders:send-introduction-reminders:delay": ConfigSettingHelp(
        description=(
            "How long to wait after a user joins your guild "
            "before sending them the first/only message "
            "to remind them to send an introduction.\n"
            "Is ignored if `reminders:send-introduction-reminders:enabled` **=** `false`.\n"
            "The delay must be longer than or equal to 1 day (in any allowed format)."
        ),
        value_type_message=_custom_required_format_message(
            (
                "string of the seconds, minutes, hours, days or weeks "
                "before the first/only reminder is sent "
                "(format: `<seconds>s<minutes>m<hours>h<days>d<weeks>w`)"
            ),
        ),
        requires_restart_after_changed=True,
        required=False,
        default=DEFAULT_SEND_INTRODUCTION_REMINDERS_DELAY,
    ),
    "reminders:send-introduction-reminders:interval": ConfigSettingHelp(
        description=(
            "The interval of time between sending out reminders "
            "to Discord members that are not inducted, "
            "saying that they need to send an introduction to be allowed access.\n"
            "Is ignored if `reminders:send-introduction-reminders:enabled` **=** `false`."
        ),
        value_type_message=_custom_required_format_message(
            (
                "string of the seconds, minutes, or hours between reminders "
                "(format: `<seconds>s<minutes>m<hours>h`)"
            ),
        ),
        requires_restart_after_changed=True,
        required=False,
        default=DEFAULT_SEND_INTRODUCTION_REMINDERS_INTERVAL,
    ),
    "reminders:send-get-roles-reminders:enabled": ConfigSettingHelp(
        description=(
            "Whether reminders will be sent to Discord members that have been inducted, "
            "saying that they can get opt-in roles. "
            "(This message will be only sent once per Discord member)."
        ),
        value_type_message=_custom_required_format_message(
            "boolean value (either `true` or `false`)",
        ),
        requires_restart_after_changed=True,
        required=False,
        default=str(DEFAULT_SEND_GET_ROLES_REMINDERS_ENABLED).lower(),
    ),
    "reminders:send-get-roles-reminders:delay": ConfigSettingHelp(
        description=(
            "How long to wait after a user is inducted "
            "before sending them the message to get some opt-in roles.\n"
            "Is ignored if `reminders:send-get-roles-reminders:enabled` **=** `false`.\n"
            "The delay must be longer than or equal to 1 day (in any allowed format)."
        ),
        value_type_message=_custom_required_format_message(
            (
                "string of the seconds, minutes, hours, days or weeks "
                "before the first/only reminder is sent "
                "(format: `<seconds>s<minutes>m<hours>h<days>d<weeks>w`)"
            ),
        ),
        requires_restart_after_changed=True,
        required=False,
        default=DEFAULT_SEND_GET_ROLES_REMINDERS_DELAY,
    ),
    "reminders:send-get-roles-reminders:interval": ConfigSettingHelp(
        description=(
            "The interval of time between sending out reminders "
            "to Discord members that have been inducted, "
            "saying that they can get opt-in roles. "
            "(This message will be only sent once, "
            "the interval is just how often to check for new guests).\n"
            "Is ignored if `reminders:send-get-roles-reminders:enabled` **=** `false`."
        ),
        value_type_message=_custom_required_format_message(
            (
                "string of the seconds, minutes, or hours between reminders "
                "(format: `<seconds>s<minutes>m<hours>h`)"
            ),
        ),
        requires_restart_after_changed=True,
        required=False,
        default=DEFAULT_SEND_GET_ROLES_REMINDERS_INTERVAL,
    ),
}

# {  # TODO: Use in config reloader
#     config_setting_name
#     for config_setting_name, config_setting_help
#     in CONFIG_SETTINGS_HELPS.items()
#     if config_setting_help.requires_restart_after_changed
# }
