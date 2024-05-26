from collections.abc import Sequence

__all__: Sequence[str] = (
    "DiscordWebhookURLValidator",
    "LogLevelValidator",
    "DiscordSnowflakeValidator",
    "RegexMatcher",
    "ProbabilityValidator",
    "TimeDeltaValidator",
    "SendIntroductionRemindersFlagValidator",
)


import functools
import math
import re
from datetime import timedelta
from typing import Final, NoReturn, override, Callable
from re import Match

import strictyaml
from strictyaml import constants as strictyaml_constants
from strictyaml import utils as strictyaml_utils
from strictyaml.exceptions import YAMLSerializationError
from strictyaml.yamllocation import YAMLChunk

from ..constants import (
    LogLevels,
    VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES,
    SendIntroductionRemindersFlagType,
)


class LogLevelValidator(strictyaml.ScalarValidator):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> LogLevels:  # type: ignore[no-any-unimported,misc]
        val: str = str(chunk.contents).upper().strip().strip("-").strip("_").strip(".")

        if val not in LogLevels:
            chunk.expecting_but_found(
                (
                    "when expecting a valid log-level "
                    f"(one of: \"{"\", \"".join(LogLevels)}\")"
                ),
            )
            raise RuntimeError

        return val  # type: ignore[return-value]

    # noinspection PyOverrides
    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        self.should_be_string(data, "expected a valid log-level.")
        str_data: str = data.upper().strip().strip("-").strip("_").strip(".")  # type: ignore[attr-defined]

        if str_data not in LogLevels:
            raise YAMLSerializationError(
                f"Got {data} when expecting one of: \"{"\", \"".join(LogLevels)}\".",
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

        DATA_IS_VALID: Final[bool] = bool(
            (
                self.__is_absolute_url(data)
                and data.startswith("https://discord.com/api/webhooks/")  # type: ignore[attr-defined]
            ),
        )
        if not DATA_IS_VALID:
            raise YAMLSerializationError(f"'{data}' is not a Discord webhook URL.")

        return data  # type: ignore[return-value]


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


class RegexMatcher(strictyaml.ScalarValidator):  # type: ignore[no-any-unimported,misc]
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

        return chunk.contents  # type: ignore[no-any-return]

    # noinspection PyOverrides
    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        self.should_be_string(data, self.MATCHING_MESSAGE)

        try:
            re.compile(data)  # type: ignore[call-overload]
        except re.error:
            raise YAMLSerializationError(f"{self.MATCHING_MESSAGE} found '{data}'")

        return data  # type: ignore[return-value]


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
            if not 0 <= data <= 100:  # type: ignore[operator]
                raise YAML_SERIALIZATION_ERROR

            if math.isnan(data):  # type: ignore[arg-type]
                return "nan"
            if data == float("inf"):
                return "inf"
            if data == float("-inf"):
                return "-inf"

            return str(data / 100)  # type: ignore[operator]

        if strictyaml_utils.is_string(data) and strictyaml_utils.is_decimal(data):
            float_data: float = float(str(data))

            if not 0 <= float_data <= 100:
                raise YAML_SERIALIZATION_ERROR

            return str(float_data / 100)

        raise YAML_SERIALIZATION_ERROR


class TimeDeltaValidator(strictyaml.ScalarValidator):  # type: ignore[no-any-unimported,misc]
    @override
    def __init__(self, *, minutes: bool = True, hours: bool = True, days: bool = False, weeks: bool = False) -> None:  # noqa: E501
        regex_matcher: str = r"\A"

        time_resolution_name: str
        for time_resolution_name in ("seconds", "minutes", "hours", "days", "weeks"):
            time_resolution_name = time_resolution_name.lower().strip()
            time_resolution: object = (
                True if time_resolution_name == "seconds" else locals()[time_resolution_name]
            )

            if not isinstance(time_resolution, bool):
                raise TypeError

            if not time_resolution:
                continue

            regex_matcher += (
                r"(?:(?P<"
                + time_resolution_name
                + r">(?:\d*\.)?\d+)"
                + time_resolution_name[0]
                + ")?"
            )

        regex_matcher += r"\Z"

        self.regex_matcher: re.Pattern[str] = re.compile(regex_matcher)

    def _get_value_from_match(self, match: Match[str], key: str) -> float:
        if key not in self.regex_matcher.groupindex.keys():
            return 0.0

        value: str | None = match.group(key)

        if not value:
            return 0.0

        float_conversion_error: ValueError
        try:
            return float(value)
        except ValueError as float_conversion_error:
            raise float_conversion_error from float_conversion_error

    @override
    def validate_scalar(self, chunk: YAMLChunk) -> timedelta:  # type: ignore[no-any-unimported,misc]
        chunk_error_func: Callable[[], NoReturn] = functools.partial(
            chunk.expecting_but_found,
            expecting="when expecting a delay/interval string",
            found="found non-matching string",
        )

        match: Match[str] | None = self.regex_matcher.match(chunk.contents)
        if match is None:
            chunk_error_func()

        try:
            return timedelta(
                seconds=self._get_value_from_match(match, "seconds"),
                minutes=self._get_value_from_match(match, "minutes"),
                hours=self._get_value_from_match(match, "hours"),
                days=self._get_value_from_match(match, "days"),
                weeks=self._get_value_from_match(match, "weeks"),
            )
        except ValueError:
            chunk_error_func()

    # noinspection PyOverrides
    @override
    def to_yaml(self, data: object) -> str:  # type: ignore[misc]
        if strictyaml_utils.is_string(data):
            match: Match[str] | None = self.regex_matcher.match(str(data))
            if match is None:
                raise YAMLSerializationError(
                    f"when expecting a delay/interval string found {str(data)!r}."
                )
            return str(data)

        if not hasattr(data, "total_seconds") or not callable(getattr(data, "total_seconds")):
            raise YAMLSerializationError(
                f"when expecting a time delta object found {str(data)!r}."
            )

        total_seconds: object = getattr(data, "total_seconds")()
        if not isinstance(total_seconds, float):
            raise TypeError

        return f"{total_seconds}s"


class SendIntroductionRemindersFlagValidator(strictyaml.ScalarValidator):  # type: ignore[no-any-unimported,misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> SendIntroductionRemindersFlagType:  # type: ignore[no-any-unimported,misc]
        val: str = str(chunk.contents).lower()

        if val not in VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES:
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

        if str(data).lower() not in VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES:
            raise YAMLSerializationError(
                f"Got {data} when expecting one of: \"Once\", \"Interval\" or \"False\".",
            )

        if str(data).lower() in strictyaml_constants.TRUE_VALUES:
            return "Once"

        if str(data).lower() in strictyaml_constants.FALSE_VALUES:
            return "False"

        return str(data).lower().title()
