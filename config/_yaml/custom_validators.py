from collections.abc import Sequence

__all__: Sequence[str] = (
    "DiscordWebhookURLValidator",
    "LogLevelValidator",
    "DiscordSnowflakeValidator",
    "RegexMatcher",
    "ProbabilityValidator",
    "SendIntroductionRemindersFlagValidator",
    "SendIntroductionRemindersFlagType",
    "LogLevelType",
)

import math
import re
from typing import Final, override, Literal, TypeAlias

import strictyaml
from strictyaml import constants as strictyaml_constants
from strictyaml import utils as strictyaml_utils
from strictyaml.exceptions import YAMLSerializationError
from strictyaml.yamllocation import YAMLChunk

from ..constants import LOG_LEVELS, VALID_SEND_INTRODUCTION_REMINDERS_VALUES


SendIntroductionRemindersFlagType: TypeAlias = Literal["once", "interval", False]
LogLevelType: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


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


class RegexMatcher(strictyaml.ScalarValidator):
    MATCHING_MESSAGE: str = "when expecting a regular expression matcher"

    @override
    def validate_scalar(self, chunk: YAMLChunk) -> str:  # type: ignore[no-any-unimported,misc]
        try:
            re.compile(chunk.contents)
        except re.error:
            chunk.expecting_but_found(
                self.MATCHING_MESSAGE,
                "found arbitrary string",
            )
        else:
            return chunk.contents

    # noinspection PyOverrides
    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        self.should_be_string(data, self.MATCHING_MESSAGE)
        if not isinstance(data, str):
            raise TypeError

        try:
            re.compile(data)
        except re.error:
            raise YAMLSerializationError(f"{self.MATCHING_MESSAGE} found '{data}'")
        else:
            return data


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
