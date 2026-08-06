"""
Pydantic schema declaring every configuration setting TeX-Bot understands.

This module is the single source of truth for the deployment configuration:
the shape of `tex-bot-deployment.yaml`, the type & constraints of every setting,
each setting's default value, and the metadata used to render the `/config` command
(help text, whether a restart is required, and whether the value is a secret).

Nothing in this module reads or writes files; it only describes & validates data.

NOTE: Annotations here are deliberately *not* deferred into `if TYPE_CHECKING:` blocks.
Pydantic evaluates field annotations at model-build time,
so every name used within a field annotation must be importable at runtime.
"""

import datetime
import re
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Literal, NamedTuple, get_args

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,  # noqa: TC002  # NOTE: Pydantic resolves field annotations at runtime
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from pydantic.fields import FieldInfo


__all__: "Sequence[str]" = (
    "AutoCookieCheckingSettings",
    "CommandsSettings",
    "CommunityGroupSettings",
    "ConfigSettingMetadata",
    "ConsoleLoggingSettings",
    "DiscordAPILoggingSettings",
    "DiscordChannelLoggingSettings",
    "DiscordSettings",
    "LinksSettings",
    "LogLevel",
    "LoggingSettings",
    "MSLSettings",
    "PingCommandSettings",
    "ReminderSettings",
    "RemindersSettings",
    "SendIntroductionRemindersFlag",
    "SendIntroductionRemindersSettings",
    "SettingsSchema",
    "StatsCommandSettings",
    "StrikeCommandSettings",
    "get_settings_metadata",
)


class LogLevel(StrEnum):
    """The set of valid values for any log-level configuration setting."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


SendIntroductionRemindersFlag = Literal["once", "interval", False]


def _to_kebab_case(field_name: str) -> str:
    """Convert a Python field name into the kebab-case key used within the YAML file."""
    return field_name.replace("_", "-")


def _parse_log_level(value: object) -> object:
    """Normalise a raw log-level value, matching it case & punctuation agnostically."""
    if not isinstance(value, str):
        return value

    return value.upper().strip(" \n\t-_.")


def _parse_send_introduction_reminders_flag(value: object) -> object:
    """
    Normalise a raw send-introduction-reminders value into its canonical form.

    Truthy boolean-like values are treated as `"once"`,
    because sending a single reminder is the historic behaviour of enabling this setting.
    """
    if isinstance(value, bool):
        return "once" if value else False

    if not isinstance(value, str):
        return value

    NORMALISED_VALUE: str = value.lower().strip()

    if NORMALISED_VALUE in ("once", "interval"):
        return NORMALISED_VALUE

    if NORMALISED_VALUE in ("true", "yes", "on", "1"):
        return "once"

    if NORMALISED_VALUE in ("false", "no", "off", "0"):
        return False

    return value


_TIME_DELTA_MATCHER: "re.Pattern[str]" = re.compile(
    r"\A(?:(?P<days>(?:\d*\.)?\d+)d)?"
    r"(?:(?P<hours>(?:\d*\.)?\d+)h)?"
    r"(?:(?P<minutes>(?:\d*\.)?\d+)m)?"
    r"(?:(?P<seconds>(?:\d*\.)?\d+)s)?\Z"
)


def _parse_time_delta(value: object) -> object:
    """
    Parse a delay/interval string (in the format `<days>d<hours>h<minutes>m<seconds>s`).

    NOTE: Time resolutions must be given in descending order of size
    (so `1h30m` is accepted, whereas `30m1h` is not).

    NOTE: A deviation from the previous StrictYAML implementation, which required time
    resolutions in *ascending* order of size, so accepted `30m1h` but rejected `1h30m`.

    NOTE: A further deviation from that previous implementation:
    an empty string is rejected rather than silently parsed as a zero-length duration.
    A zero-length interval would cause any task looping upon it to spin without pausing.
    """
    if not isinstance(value, str):
        return value

    match: re.Match[str] | None = _TIME_DELTA_MATCHER.fullmatch(value.strip())
    if match is None or not any(match.groupdict().values()):
        # NOTE: Raising here (rather than deferring to Pydantic's own timedelta parsing)
        # keeps the set of accepted values identical to the documented format:
        # Pydantic would otherwise also accept ISO-8601 durations & `HH:MM:SS` strings.
        INVALID_TIME_DELTA_MESSAGE: str = (
            "Value should be a delay/interval string, in the format "
            "'<days>d<hours>h<minutes>m<seconds>s' "
            "(with time resolutions given in descending order of size)"
        )
        raise ValueError(INVALID_TIME_DELTA_MESSAGE)

    return datetime.timedelta(
        **{
            time_resolution_name: float(raw_time_resolution_value)
            for time_resolution_name, raw_time_resolution_value in match.groupdict().items()
            if raw_time_resolution_value
        }
    )


def _ensure_discord_webhook_url(value: HttpUrl) -> HttpUrl:
    """Ensure the given URL refers to a Discord webhook."""
    if not str(value).startswith("https://discord.com/api/webhooks/"):
        NOT_A_DISCORD_WEBHOOK_URL_MESSAGE: str = (
            "Value should be a Discord webhook URL "
            "(beginning with 'https://discord.com/api/webhooks/')"
        )
        raise ValueError(NOT_A_DISCORD_WEBHOOK_URL_MESSAGE)

    return value


def _ensure_matches(
    value: SecretStr, matcher: "re.Pattern[str]", expected_description: str
) -> SecretStr:
    """
    Ensure the given secret value matches the given pattern.

    The secret value itself is never included within the raised error message.
    """
    if matcher.fullmatch(value.get_secret_value()) is None:
        NON_MATCHING_VALUE_MESSAGE: str = f"Value should be {expected_description}"
        raise ValueError(NON_MATCHING_VALUE_MESSAGE)

    return value


def _ensure_unique(value: tuple[str, ...]) -> tuple[str, ...]:
    """Ensure the given sequence of values contains no duplicates."""
    if len(set(value)) != len(value):
        DUPLICATE_VALUES_MESSAGE: str = "Value should be a sequence of unique values"
        raise ValueError(DUPLICATE_VALUES_MESSAGE)

    return value


type TimeDelta = Annotated[datetime.timedelta, BeforeValidator(_parse_time_delta)]
type UniqueStrSequence = Annotated[tuple[str, ...], AfterValidator(_ensure_unique)]
type DiscordWebhookURL = Annotated[HttpUrl, AfterValidator(_ensure_discord_webhook_url)]
type DiscordSnowflake = Annotated[int, Field(ge=10**16, lt=10**20)]
type NormalisedLogLevel = Annotated[LogLevel, BeforeValidator(_parse_log_level)]


class _BaseSettingsSchema(BaseModel):
    """
    Common configuration shared by every section of the settings schema.

    NOTE: Every subclass below carries a `# type: ignore[explicit-any]` comment.
    Pydantic's `BaseModel` exposes explicit `Any` within its own API surface
    (`__init__(**data: Any)`, `model_validate(obj: Any)`, etc.),
    so subclassing it is inherently incompatible with `disallow_any_explicit`.
    The ignores are applied per-class, rather than by disabling the error code
    for this whole module, so that any genuine use of `Any` here is still caught.
    """

    model_config = ConfigDict(
        alias_generator=_to_kebab_case,
        populate_by_name=True,
        extra="forbid",
        frozen=True,
        # NOTE: Pydantic's default regex engine is Rust's, which rejects Python-only anchors
        # (such as `\Z`). Using Python's own engine keeps every pattern below identical to
        # the one it replaces, rather than requiring subtly different equivalents.
        regex_engine="python-re",
    )


class ConsoleLoggingSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling how logs are emitted to the console output stream."""

    log_level: NormalisedLogLevel = Field(
        default=LogLevel.INFO,
        description=(
            "The minimum level that logs must meet "
            "in order to be logged to the console output stream."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class DiscordChannelLoggingSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling how logs are relayed to a Discord log channel."""

    webhook_url: DiscordWebhookURL = Field(
        description=(
            "The webhook URL of the Discord text channel where error logs should be sent.\n"
            "Error logs will always be sent to the console; "
            "this setting allows them to also be sent to a Discord log channel."
        ),
        json_schema_extra={"requires_restart": False, "secret": True},
    )
    log_level: NormalisedLogLevel = Field(
        default=LogLevel.WARNING,
        description=(
            "The minimum level that logs must meet "
            "in order to be logged to the Discord log channel."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class DiscordAPILoggingSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling how logs emitted by the Discord API wrapper are handled."""

    enabled: bool = Field(
        default=False,
        description="Whether logs emitted by the Discord API wrapper should be recorded.",
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    log_level: NormalisedLogLevel = Field(
        default=LogLevel.INFO,
        description=(
            "The minimum level that Discord API logs must meet in order to be recorded."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    file_name: str = Field(
        default="discord.log",
        min_length=1,
        description="The name of the file that Discord API logs should be written to.",
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class LoggingSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling every logging destination TeX-Bot can write to."""

    console: ConsoleLoggingSettings = Field(default_factory=ConsoleLoggingSettings)
    discord_channel: DiscordChannelLoggingSettings | None = Field(
        default=None,
        description=(
            "Settings for relaying error logs to a Discord log channel. "
            "Omit this section entirely to disable Discord log-channel logging."
        ),
    )
    discord_api: DiscordAPILoggingSettings = Field(default_factory=DiscordAPILoggingSettings)


class DiscordSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings describing how TeX-Bot connects to Discord."""

    bot_token: Annotated[
        SecretStr,
        AfterValidator(
            lambda token: _ensure_matches(
                token,
                re.compile(
                    r"\A(?!.*__.*)(?!.*--.*)"
                    r"(?:([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38}))\Z"
                ),
                "a Discord bot token",
            )
        ),
    ] = Field(
        description=(
            "The Discord token for the bot you created (available on your bot's page "
            "within the Discord developer portal: "
            "<https://discord.com/developers/applications>)."
        ),
        json_schema_extra={"requires_restart": True, "secret": True},
    )
    main_guild_id: DiscordSnowflake = Field(
        description="The ID of your community group's main Discord guild.",
        json_schema_extra={"requires_restart": True, "secret": False},
    )


class LinksSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings holding the external links referenced within TeX-Bot's messages."""

    purchase_membership: HttpUrl | None = Field(
        default=None,
        description=(
            "The link to the page where guests can purchase a full membership "
            "to join your community group."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    membership_perks: HttpUrl | None = Field(
        default=None,
        description=(
            "The link to the page where guests can find out information about the perks "
            "they will receive once they purchase a membership to your community group."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    moderation_policy: HttpUrl | None = Field(
        default=None,
        description="The link to your group's Discord guild moderation policy document.",
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    custom_discord_invite_link: HttpUrl | None = Field(
        default=None,
        description=(
            "A custom invite link to your group's Discord guild, "
            "used in place of one generated by TeX-Bot."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class AutoCookieCheckingSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling the automatic checking of the MSL authentication cookie."""

    enabled: bool = Field(
        default=False,
        description=(
            "Whether the MSL authentication cookie should be automatically checked "
            "to determine whether it is still valid."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    interval: TimeDelta = Field(
        default=datetime.timedelta(minutes=10),
        description="The interval of time between checking the MSL authentication cookie.",
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class MSLSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings describing how TeX-Bot authenticates with your group's MSL website."""

    organisation_id: str | None = Field(
        default=None,
        pattern=r"\A\d{4,5}\Z",
        description="The ID of your community group's organisation on your MSL website.",
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    auth_cookie: (
        Annotated[
            SecretStr,
            AfterValidator(
                lambda cookie: _ensure_matches(
                    cookie,
                    re.compile(r"\A[\w-]{512,1024}\Z"),
                    "an MSL authentication cookie",
                )
            ),
        ]
        | None
    ) = Field(
        default=None,
        description=(
            "The MSL authentication session cookie.\n"
            "This should authenticate TeX-Bot to view your group's members-list, "
            "as if it were logged in to the website as a committee member.\n"
            "If your members-list is found on the UoB Guild of Students website, "
            "this can be extracted from your web-browser after manually logging in: "
            "it will probably be listed as a cookie named `.ASPXAUTH`."
        ),
        json_schema_extra={"requires_restart": False, "secret": True},
    )
    auto_cookie_checking: AutoCookieCheckingSettings = Field(
        default_factory=AutoCookieCheckingSettings
    )


class CommunityGroupSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings describing the community group that TeX-Bot is deployed for."""

    full_name: str | None = Field(
        default=None,
        pattern=r"\A.{1,50}\Z",
        description=(
            "The full name of your community group; do **NOT** use an abbreviation.\n"
            "This is substituted into many error/welcome messages "
            "sent into your Discord guild by TeX-Bot.\n"
            "If this is not set, the group's full name will be retrieved "
            "from the name of your group's Discord guild."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    short_name: str | None = Field(
        default=None,
        pattern=r"\A(?!.*['&!?:,.#%\"-]['&!?:,.#%\"-].*)(?:[A-Za-z0-9'&!?:,.#%\"-]+)\Z",
        description=(
            "The short colloquial name of your community group; it is recommended "
            "that you set this to be an abbreviation of your group's name.\n"
            "If this is not set, the group's short name will be determined "
            "from your group's full name."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    membership_dependent_roles: UniqueStrSequence = Field(
        # NOTE: Defaults to no roles, rather than being absent, so that consumers can
        # always iterate it or test membership of it without a null check first.
        default=(),
        description=(
            "The names of the roles that should only be held "
            "by members of your community group."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    links: LinksSettings
    msl: MSLSettings


class PingCommandSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling the behaviour of the `/ping` command."""

    easter_egg_probability: float = Field(
        default=0.01,
        ge=0,
        le=1,
        description=(
            "The probability that the rarer ping command response will be sent "
            "instead of the normal one."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class StatsCommandSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling the behaviour of the `/stats` command."""

    lookback_days: float = Field(
        default=30.0,
        ge=5,
        le=1826,
        description=(
            "The number of days to look back over messages sent, to generate statistics data."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    displayed_roles: UniqueStrSequence = Field(
        default=(
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
        ),
        description=(
            "The names of the roles to gather statistics about, to display in bar charts."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )

    @property
    def lookback_period(self) -> datetime.timedelta:
        """
        The period of time to look back over messages sent, to generate statistics data.

        Held within the configuration file as a plain number of days, because that reads
        far more naturally than a duration string for a value of this size.
        """
        return datetime.timedelta(days=self.lookback_days)


class StrikeCommandSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling the behaviour of the `/strike` command."""

    performed_manually_warning_location: str = Field(
        default="DM",
        min_length=1,
        description=(
            "The name of the channel that warning messages will be sent to, when a "
            "committee-member manually applies a moderation action "
            "(instead of using the `/strike` command).\n"
            "This can be the name of **ANY** Discord channel "
            "(so the offending person *will* be able to see these messages "
            "if a public channel is chosen), or the value `DM` "
            "(which indicates the messages will be sent to the committee-member's DMs)."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    timeout_duration: TimeDelta = Field(
        default=datetime.timedelta(hours=24),
        description=(
            "The amount of time to timeout a user for, when using the `/strike` command."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    reported_message_destination_channel: str = Field(
        default="discord",
        min_length=1,
        description=(
            "The name of the channel that reported messages should be sent to for review."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class CommandsSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling the behaviour of TeX-Bot's individual commands."""

    ping: PingCommandSettings = Field(default_factory=PingCommandSettings)
    stats: StatsCommandSettings = Field(default_factory=StatsCommandSettings)
    strike: StrikeCommandSettings = Field(default_factory=StrikeCommandSettings)


class SendIntroductionRemindersSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling the reminders sent to Discord members that are not inducted."""

    enabled: Annotated[
        SendIntroductionRemindersFlag,
        BeforeValidator(_parse_send_introduction_reminders_flag),
    ] = Field(
        default="once",
        description=(
            "Whether introduction reminders will be sent to Discord members "
            "that are not inducted, saying that they need to send an introduction "
            "to be allowed access.\n"
            "Use `once` to send a single reminder, `interval` to send them repeatedly, "
            "or `false` to disable them entirely."
        ),
        json_schema_extra={"requires_restart": True, "secret": False},
    )
    delay: TimeDelta = Field(
        default=datetime.timedelta(hours=40),
        description=(
            "How long to wait after a user joins your guild, before sending them "
            "the first/only message reminding them to send an introduction.\n"
            "Is ignored if `enabled` **=** `false`."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    interval: TimeDelta = Field(
        default=datetime.timedelta(hours=6),
        description=(
            "The interval of time between sending out reminders to Discord members "
            "that are not inducted.\n"
            "Is ignored unless `enabled` **=** `interval`."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class ReminderSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling the reminders sent to Discord members that have been inducted."""

    enabled: bool = Field(
        default=True,
        description=(
            "Whether reminders will be sent to Discord members that have been inducted, "
            "saying that they can get opt-in roles. "
            "(This message will only be sent once per Discord member.)"
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    delay: TimeDelta = Field(
        default=datetime.timedelta(hours=40),
        description=(
            "How long to wait after a user is inducted, before sending them the message "
            "telling them to get some opt-in roles.\n"
            "Is ignored if `enabled` **=** `false`."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )
    interval: TimeDelta = Field(
        default=datetime.timedelta(hours=6),
        description=(
            "The interval of time between checking for Discord members "
            "that should be sent a get-roles reminder.\n"
            "Is ignored if `enabled` **=** `false`."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class RemindersSettings(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """Settings controlling every kind of reminder that TeX-Bot can send."""

    send_introduction_reminders: SendIntroductionRemindersSettings = Field(
        default_factory=SendIntroductionRemindersSettings
    )
    send_get_roles_reminders: ReminderSettings = Field(default_factory=ReminderSettings)


class SettingsSchema(_BaseSettingsSchema):  # type: ignore[explicit-any]
    """The complete set of configuration settings that TeX-Bot understands."""

    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    discord: DiscordSettings
    community_group: CommunityGroupSettings
    commands: CommandsSettings = Field(default_factory=CommandsSettings)
    reminders: RemindersSettings = Field(default_factory=RemindersSettings)
    auto_add_committee_to_threads: bool = Field(
        default=True,
        description=(
            "Whether committee members should be automatically added "
            "to any newly created threads."
        ),
        json_schema_extra={"requires_restart": False, "secret": False},
    )


class ConfigSettingMetadata(NamedTuple):
    """The information describing a single configuration setting to a human."""

    description: str | None
    requires_restart: bool
    secret: bool


def _walk_settings_metadata(
    model: type[BaseModel], prefix: str = ""
) -> "Iterator[tuple[str, ConfigSettingMetadata]]":
    """Yield the metadata of every individual setting declared within the given model."""
    field_name: str
    field: FieldInfo
    for field_name, field in model.model_fields.items():
        KEY_PATH: str = f"{prefix}{field_name.replace('_', '-')}"

        # NOTE: A field's annotation may be a union (an optional section, for example), so
        # every member of it must be searched to find the nested model it may contain.
        nested_model: type[BaseModel] | None = next(
            (
                annotation_argument
                for annotation_argument in (get_args(field.annotation) or (field.annotation,))
                if isinstance(annotation_argument, type)
                and issubclass(annotation_argument, BaseModel)
            ),
            None,
        )
        if nested_model is not None:
            yield from _walk_settings_metadata(nested_model, prefix=f"{KEY_PATH}:")
            continue

        EXTRA: Mapping[str, object] = (
            field.json_schema_extra if isinstance(field.json_schema_extra, dict) else {}
        )

        yield (
            KEY_PATH,
            ConfigSettingMetadata(
                description=field.description,
                requires_restart=EXTRA.get("requires_restart") is True,
                secret=EXTRA.get("secret") is True,
            ),
        )


def get_settings_metadata() -> "Mapping[str, ConfigSettingMetadata]":
    """
    Return the metadata of every configuration setting, keyed by its key path.

    Derived from the schema itself, so that the help text, restart requirements &
    secrecy of each setting cannot drift out of step with the settings that exist.
    """
    return dict(_walk_settings_metadata(SettingsSchema))
