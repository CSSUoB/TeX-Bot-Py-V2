from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final, Literal, NoReturn

    from strictyaml.yamllocation import YAMLChunk

    from config.constants import (
        SendIntroductionRemindersFlagType,
    )

__all__: "Sequence[str]" = (
    "BoundedFloatValidator",
    "CustomBoolValidator",
    "DiscordSnowflakeValidator",
    "DiscordWebhookURLValidator",
    "LogLevelValidator",
    "RegexMatcher",
    "SendIntroductionRemindersFlagValidator",
    "TimeDeltaValidator",
)


import datetime
import functools
import math
import re
from typing import TYPE_CHECKING, override

import strictyaml
from strictyaml import constants as strictyaml_constants
from strictyaml import utils as strictyaml_utils
from strictyaml.exceptions import YAMLSerializationError

from config.constants import (
    VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES,
    LogLevels,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class LogLevelValidator(strictyaml.ScalarValidator):
    @override
    def validate_scalar(self, chunk: "YAMLChunk") -> LogLevels:
        val: str = str(chunk.contents).upper().strip(" \n\t-_.")

        if val not in LogLevels:
            chunk.expecting_but_found(
                f"when expecting a valid log-level (one of: '{"', '".join(LogLevels)}')",
            )
            raise RuntimeError

        return val  # type: ignore[return-value]

    @override
    def to_yaml(self, data: object) -> str:
        self.should_be_string(data, "expected a valid log-level.")
        str_data: str = data.upper().strip(" \n\t-_.")  # type: ignore[attr-defined]

        if str_data not in LogLevels:
            INVALID_DATA_MESSAGE: Final[str] = (
                f"Got '{data}' when expecting one of: '{"', '".join(LogLevels)}'."
            )
            raise YAMLSerializationError(INVALID_DATA_MESSAGE)

        return str_data


class DiscordWebhookURLValidator(strictyaml.Url):
    @override
    def validate_scalar(self, chunk: "YAMLChunk") -> str:
        CHUNK_IS_VALID: Final[bool] = bool(
            self._Url__is_absolute_url(chunk.contents)
            and chunk.contents.startswith("https://discord.com/api/webhooks/")
        )
        if not CHUNK_IS_VALID:
            chunk.expecting_but_found("when expecting a Discord webhook URL")
            raise RuntimeError

        return chunk.contents  # type: ignore[no-any-return]

    @override
    def to_yaml(self, data: object) -> str:
        self.should_be_string(data, "expected a URL,")

        # noinspection PyUnresolvedReferences
        DATA_IS_VALID: Final[bool] = bool(
            self._Url__is_absolute_url(data)
            and data.startswith("https://discord.com/api/webhooks/")  # type: ignore[attr-defined]
        )
        if not DATA_IS_VALID:
            INVALID_DATA_MESSAGE: Final[str] = f"'{data}' is not a Discord webhook URL."
            raise YAMLSerializationError(INVALID_DATA_MESSAGE)

        return data  # type: ignore[return-value]


class DiscordSnowflakeValidator(strictyaml.Int):
    @override
    def validate_scalar(self, chunk: "YAMLChunk") -> int:
        val: int = super().validate_scalar(chunk)

        if not re.fullmatch(r"\A\d{17,20}\Z", str(val)):
            chunk.expecting_but_found("when expecting a Discord snowflake ID")
            raise RuntimeError

        return val

    @override
    def to_yaml(self, data: object) -> str:
        DATA_IS_VALID: Final[bool] = bool(
            (strictyaml_utils.is_string(data) or isinstance(data, int))
            and strictyaml_utils.is_integer(str(data))
            and re.fullmatch(r"\A\d{17,20}\Z", str(data))
        )
        if not DATA_IS_VALID:
            INVALID_DATA_MESSAGE: Final[str] = f"'{data}' is not a Discord snowflake ID."
            raise YAMLSerializationError(INVALID_DATA_MESSAGE)

        return str(data)


class RegexMatcher(strictyaml.ScalarValidator):
    MATCHING_MESSAGE: str = "when expecting a regular expression matcher"

    @override
    def validate_scalar(self, chunk: "YAMLChunk") -> str:
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
    def to_yaml(self, data: object) -> str:
        self.should_be_string(data, self.MATCHING_MESSAGE)

        regex_error: re.error
        try:
            re.compile(data)  # type: ignore[call-overload]
        except re.error as regex_error:
            INVALID_DATA_MESSAGE: Final[str] = f"{self.MATCHING_MESSAGE} found '{data}'"
            raise YAMLSerializationError(INVALID_DATA_MESSAGE) from regex_error

        return data  # type: ignore[return-value]


class BoundedFloatValidator(strictyaml.Float):
    @override
    def __init__(self, inclusive_minimum: float, inclusive_maximum: float) -> None:
        self.inclusive_minimum: float = inclusive_minimum
        self.inclusive_maximum: float = inclusive_maximum

        super().__init__()

    @override
    def validate_scalar(self, chunk: "YAMLChunk") -> float:
        val: float = super().validate_scalar(chunk)

        if not self.inclusive_minimum <= val <= self.inclusive_maximum:
            chunk.expecting_but_found(
                (
                    "when expecting a float "
                    f"between {self.inclusive_minimum} & {self.inclusive_maximum}"
                ),
            )
            raise RuntimeError

        return val

    @override
    def to_yaml(self, data: object) -> str:
        YAML_SERIALIZATION_ERROR: Final[YAMLSerializationError] = YAMLSerializationError(
            (
                f"'{data}' is not a float "
                f"between {self.inclusive_minimum} & {self.inclusive_maximum}."
            ),
        )

        if strictyaml_utils.is_string(data) and strictyaml_utils.is_decimal(data):
            data = float(str(data))

        if not strictyaml_utils.has_number_type(data):
            raise YAML_SERIALIZATION_ERROR

        if not self.inclusive_minimum <= data <= self.inclusive_maximum:  # type: ignore[operator]
            raise YAML_SERIALIZATION_ERROR

        if math.isnan(data):  # type: ignore[arg-type]
            return "nan"
        if data == float("inf"):
            return "inf"
        if data == float("-inf"):
            return "-inf"

        return str(data)


class TimeDeltaValidator(strictyaml.ScalarValidator):
    @override
    def __init__(
        self,
        *,
        seconds: "Literal[True]" = True,
        minutes: bool = True,
        hours: bool = True,
        days: bool = False,
        weeks: bool = False,
    ) -> None:
        regex_matcher: str = r"\A"

        time_resolution_name: str
        for time_resolution_name in ("seconds", "minutes", "hours", "days", "weeks"):
            formatted_time_resolution_name: str = time_resolution_name.lower().strip()
            time_resolution: object = locals()[formatted_time_resolution_name]

            if not isinstance(time_resolution, bool):
                raise TypeError

            if not time_resolution:
                continue

            regex_matcher += (
                r"(?:(?P<"
                + formatted_time_resolution_name
                + r">(?:\d*\.)?\d+)"
                + formatted_time_resolution_name[0]
                + ")?"
            )

        regex_matcher += r"\Z"

        self.regex_matcher: re.Pattern[str] = re.compile(regex_matcher)

    def _get_value_from_match(self, match: "re.Match[str]", key: str) -> float:
        if key not in self.regex_matcher.groupindex:
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
    def validate_scalar(self, chunk: "YAMLChunk") -> datetime.timedelta:
        chunk_error_func: Callable[[], NoReturn] = functools.partial(
            chunk.expecting_but_found,
            expecting="when expecting a delay/interval string",
            found="found non-matching string",
        )

        match: re.Match[str] | None = self.regex_matcher.fullmatch(chunk.contents)
        if match is None:
            chunk_error_func()

        try:
            return datetime.timedelta(
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
    def to_yaml(self, data: object) -> str:
        if strictyaml_utils.is_string(data):
            match: re.Match[str] | None = self.regex_matcher.fullmatch(str(data))
            if match is None:
                INVALID_STRING_DATA_MESSAGE: Final[str] = (
                    f"when expecting a delay/interval string found {str(data)!r}."
                )
                raise YAMLSerializationError(INVALID_STRING_DATA_MESSAGE)
            return str(data)

        if not hasattr(data, "total_seconds") or not callable(getattr(data, "total_seconds")):  # noqa: B009
            INVALID_TIMEDELTA_DATA_MESSAGE: Final[str] = (
                f"when expecting a time delta object found {str(data)!r}."
            )
            raise YAMLSerializationError(INVALID_TIMEDELTA_DATA_MESSAGE)

        total_seconds: object = getattr(data, "total_seconds")()  # noqa: B009
        if not isinstance(total_seconds, float):
            raise TypeError

        if (total_seconds / 3600) % 1 == 0:
            return f"{int(total_seconds / 3600)}h"

        if total_seconds % 1 == 0:
            return f"{int(total_seconds)}s"

        return f"{total_seconds}s"


class SendIntroductionRemindersFlagValidator(strictyaml.ScalarValidator):
    @override
    def validate_scalar(self, chunk: "YAMLChunk") -> "SendIntroductionRemindersFlagType":
        val: str = str(chunk.contents).lower()

        if val not in VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES:
            chunk.expecting_but_found(
                (
                    "when expecting a send-introduction-reminders-flag "
                    "(one of: 'once', 'interval' or 'false')"
                ),
            )
            raise RuntimeError

        if val in strictyaml_constants.TRUE_VALUES:
            return "once"

        if val not in ("once", "interval"):
            return False

        return val  # type: ignore[return-value]

    @override
    def to_yaml(self, data: object) -> str:
        if isinstance(data, bool):
            return "once" if data else "false"

        if str(data).lower() not in VALID_SEND_INTRODUCTION_REMINDERS_RAW_VALUES:
            INVALID_DATA_MESSAGE: Final[str] = (
                f"Got '{data}' when expecting one of: 'once', 'interval' or 'false'."
            )
            raise YAMLSerializationError(INVALID_DATA_MESSAGE)

        if str(data).lower() in strictyaml_constants.TRUE_VALUES:
            return "once"

        if str(data).lower() in strictyaml_constants.FALSE_VALUES:
            return "false"

        return str(data).lower()


class CustomBoolValidator(strictyaml.Bool):
    @override
    def to_yaml(self, data: object) -> str:
        if isinstance(data, bool):
            return "true" if data else "false"

        if str(data).lower() in strictyaml_constants.TRUE_VALUES:
            return "true"

        if str(data).lower() in strictyaml_constants.FALSE_VALUES:
            return "false"

        INVALID_TYPE_MESSAGE: Final[str] = "Not a boolean"
        raise YAMLSerializationError(INVALID_TYPE_MESSAGE)
