from collections.abc import Sequence

__all__: Sequence[str] = (
    "SlugValidator",
    "DiscordWebhookURLValidator",
    "SETTINGS_YAML_SCHEMA",
    "load_yaml",
)

import math
import re
from typing import Final, Literal, TypeAlias, override

import slugify
import strictyaml
from strictyaml import YAML, constants as strictyaml_constants
from strictyaml import utils as strictyaml_utils
from strictyaml.exceptions import YAMLSerializationError
from strictyaml.yamllocation import YAMLChunk

from .constants import (
    DEFAULT_STATISTICS_ROLES,
    LOG_LEVELS,
    TRANSLATED_MESSAGES_LOCALE_CODES,
    VALID_SEND_INTRODUCTION_REMINDERS_VALUES,
)

SendIntroductionRemindersFlagType: TypeAlias = Literal["once", "interval", False]
LogLevelType: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SlugValidator(strictyaml.ScalarValidator):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> str:  # type: ignore[no-any-unimported,misc]
        return slugify.slugify(str(chunk.contents))


class LogLevelValidator(strictyaml.ScalarValidator):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> LogLevelType:  # type: ignore[no-any-unimported,misc]
        val: str = str(chunk.contents).upper()

        if val not in LOG_LEVELS:
            chunk.expecting_but_found(
                (
                    "when expecting a valid log-level "
                    f"(one of: \"{"\", \"".join(LOG_LEVELS)}\")"
                ),
            )
            raise RuntimeError

        return val  # type: ignore[return-value]

    # noinspection PyOverrides
    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        str_data: str = str(data).upper()

        if str_data.upper() not in LOG_LEVELS:
            raise YAMLSerializationError(
                f"Got {data} when expecting one of: \"{"\", \"".join(LOG_LEVELS)}\".",
            )

        return str_data


class DiscordWebhookURLValidator(strictyaml.Url):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> str:  # type: ignore[no-any-unimported,misc]
        CHUNK_IS_VALID: Final[bool] = bool(
            (
                self.__is_absolute_url(chunk.contents)
                and chunk.contents.startswith("https://discord.com/api/webhooks/")
            ),
        )
        if not CHUNK_IS_VALID:
            chunk.expecting_but_found("when expecting a Discord webhook URL")
            raise RuntimeError

        return chunk.contents  # type: ignore[no-any-return]

    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        self.should_be_string(data, "expected a URL,")

        if not isinstance(data, str):
            raise TypeError

        DATA_IS_VALID: Final[bool] = bool(
            (
                self.__is_absolute_url(data)
                and data.startswith("https://discord.com/api/webhooks/")
            ),
        )
        if not DATA_IS_VALID:
            raise YAMLSerializationError(f"'{data}' is not a Discord webhook URL.")

        return data


class DiscordSnowflakeValidator(strictyaml.Int):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> int:  # type: ignore[no-any-unimported,misc]
        val: int = super().validate_scalar(chunk)

        if not re.match(r"\A\d{17,20}\Z", str(val)):
            chunk.expecting_but_found("when expecting a Discord snowflake ID")
            raise RuntimeError

        return val

    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        DATA_IS_VALID: Final[bool] = bool(
            (
                (strictyaml_utils.is_string(data) or isinstance(data, int))
                and strictyaml_utils.is_integer(str(data))
                and re.match(r"\A\d{17,20}\Z", str(data))
            ),
        )
        if not DATA_IS_VALID:
            raise YAMLSerializationError(f"'{data}' is not a Discord snowflake ID.")

        return str(data)


class ProbabilityValidator(strictyaml.Float):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> float:  # type: ignore[no-any-unimported,misc]
        val: float = 100 * super().validate_scalar(chunk)

        if not 0 <= val <= 100:
            chunk.expecting_but_found("when expecting a probability")
            raise RuntimeError

        return val

    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        YAML_SERIALIZATION_ERROR: Final[YAMLSerializationError] = YAMLSerializationError(  # type: ignore[no-any-unimported]
            f"'{data}' is not a probability.",
        )

        if strictyaml_utils.has_number_type(data):
            if not isinstance(data, float):
                raise TypeError

            if not 0 <= data <= 100:
                raise YAML_SERIALIZATION_ERROR

            if math.isnan(data):
                return "nan"
            if data == float("inf"):
                return "inf"
            if data == float("-inf"):
                return "-inf"

            return str(data / 100)

        if strictyaml_utils.is_string(data) and strictyaml_utils.is_decimal(data):
            if not isinstance(data, str):
                raise TypeError

            float_data: float = float(data)

            if not 0 <= float_data <= 100:
                raise YAML_SERIALIZATION_ERROR

            return str(float_data / 100)

        raise YAML_SERIALIZATION_ERROR


class SendIntroductionRemindersFlagValidator(strictyaml.ScalarValidator):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> SendIntroductionRemindersFlagType:  # type: ignore[no-any-unimported,misc]
        val: str = str(chunk.contents).lower()

        if val not in VALID_SEND_INTRODUCTION_REMINDERS_VALUES:
            chunk.expecting_but_found(
                (
                    "when expecting a send-introduction-reminders-flag "
                    "(one of: \"Once\", \"Interval\" or \"False\")"
                ),
            )
            raise RuntimeError

        if val in strictyaml_constants.TRUE_VALUES:
            return "once"

        if val not in ("once", "interval"):
            return False

        return val  # type: ignore[return-value]

    # noinspection PyOverrides
    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        if isinstance(data, bool):
            return "Once" if data else "False"

        if not isinstance(data, str) or data not in VALID_SEND_INTRODUCTION_REMINDERS_VALUES:
            raise YAMLSerializationError(
                f"Got {data} when expecting one of: \"Once\", \"Interval\" or \"False\".",
            )

        if data in strictyaml_constants.TRUE_VALUES:
            return "Once"

        if data in strictyaml_constants.FALSE_VALUES:
            return "False"

        return data.title()


SETTINGS_YAML_SCHEMA: Final[strictyaml.Map] = strictyaml.Map(  # type: ignore[no-any-unimported]
    {
        strictyaml.Optional("console-log-level", default="INFO"): LogLevelValidator(),
        strictyaml.Optional("discord-log-channel-log-level", default="WARNING"): (
            LogLevelValidator()
        ),
        "discord-bot-token": strictyaml.Regex(
            r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z",
        ),
        strictyaml.Optional("discord-log-channel-webhook-url"): DiscordWebhookURLValidator(),
        "discord-guild-id": DiscordSnowflakeValidator(),
        strictyaml.Optional("group-full-name"): strictyaml.Regex(
            r"\A[A-Za-z0-9 '&!?:,.#%\"-]+\Z",
        ),
        strictyaml.Optional("group-short-name"): strictyaml.Regex(
            r"\A[A-Za-z0-9'&!?:,.#%\"-]+\Z",
        ),
        strictyaml.Optional("purchase-membership-url"): strictyaml.Url(),
        strictyaml.Optional("membership-perks-url"): strictyaml.Url(),
        strictyaml.Optional("ping-command-easter-egg-probability", default=0.01): (
            ProbabilityValidator()
        ),
        strictyaml.Optional("messages-language", default="en-GB"): strictyaml.Enum(
            TRANSLATED_MESSAGES_LOCALE_CODES,
        ),
        "members-list-url": strictyaml.Url(),
        "members-list-url-session-cookie": strictyaml.Str(),
        strictyaml.Optional("send-introduction-reminders", default="once"): (
            SendIntroductionRemindersFlagValidator()
        ),
        strictyaml.Optional("send-introduction-reminders-delay", default="40h"): (
            strictyaml.Regex(
                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
            )
        ),
        strictyaml.Optional("send-introduction-reminders-interval", default="6h"): (
            strictyaml.Regex(
                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
            )
        ),
        strictyaml.Optional("send-get-roles-reminders", default=True): strictyaml.Bool(),
        strictyaml.Optional("send-get-roles-reminders-delay", default="40h"): (
            strictyaml.Regex(
                r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
            )
        ),
        strictyaml.Optional("statistics-days", default=30.0): strictyaml.Float(),
        strictyaml.Optional("statistics-roles", default=list(DEFAULT_STATISTICS_ROLES)): (
            strictyaml.UniqueSeq(strictyaml.Str())
        ),
        "moderation-document-url": strictyaml.Url(),
        strictyaml.Optional("manual-moderation-warning-message-location", default="DM"): (
            strictyaml.Str()
        ),
        strictyaml.Optional("strike-timeout-duration", default="24h"): strictyaml.Regex(
            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z",
        ),
        strictyaml.Optional("group-member-id-format", default=r"\A\d{7}\Z"): (
            strictyaml.Str()
        ),
        strictyaml.Optional("advanced", default={}): strictyaml.EmptyDict() | (
            strictyaml.Map(
                {
                    strictyaml.Optional("send-get-roles-reminders-interval", default="6h"): (
                        strictyaml.Regex(
                            r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z",
                        )
                    ),
                },
                key_validator=SlugValidator(),
            )
        ),
    },
    key_validator=SlugValidator(),
)


def load_yaml(raw_yaml: str) -> YAML:
    parsed_yaml: YAML = strictyaml.load(raw_yaml, SETTINGS_YAML_SCHEMA)  # type: ignore[no-any-unimported]

    # noinspection SpellCheckingInspection
    if "guildofstudents" in parsed_yaml["members-list-url"]:
        parsed_yaml["members-list-url-session-cookie"].revalidate(
            strictyaml.Regex(r"\A[A-Fa-f\d]{128,256}\Z"),
        )

    return parsed_yaml
