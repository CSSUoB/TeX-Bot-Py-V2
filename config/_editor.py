"""
Changing individual settings within the deployment configuration file.

Every change is applied to a copy of the configuration document & validated before
anything is written, so that a mistaken value can never leave TeX-Bot holding a
configuration file it would refuse to load.

This module holds no knowledge of Discord: it turns the text a committee member typed
into a value, decides whether that value is acceptable, & renders values back into
something readable. Doing so here (rather than within the `/config` command itself)
keeps all of it testable without a connection to Discord.
"""

import datetime
from typing import TYPE_CHECKING

from pydantic import SecretStr, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ._accessor import SettingsValidationError
from ._document import SettingsDocument
from ._schema import SettingsSchema, get_settings_metadata

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final

    from ._schema import ConfigSettingMetadata


__all__: "Sequence[str]" = (
    "SETTING_NAME_SEPARATOR",
    "UnknownSettingError",
    "documented_setting_names",
    "format_setting_value",
    "parse_setting_value",
    "setting_metadata",
    "validated_document_with_setting_removed",
    "validated_document_with_setting_set",
)


SETTING_NAME_SEPARATOR: "Final[str]" = ":"

REDACTED_VALUE_DISPLAY: "Final[str]" = "\\*\\*\\*\\*\\*\\* _(hidden)_"

UNSET_VALUE_DISPLAY: "Final[str]" = "_(not set)_"

# NOTE: Anything YAML would read back as a value other than a string, so that a value
# given as one of these words is not written into the file as bare text.
_NULL_LITERALS: "Final[frozenset[str]]" = frozenset({"null", "~"})


class UnknownSettingError(Exception):
    """Exception class to raise when a setting that the schema does not declare is named."""

    def __init__(self, setting_name: str) -> None:
        """Initialise a new UnknownSettingError for the given setting name."""
        self.setting_name: str = setting_name

        super().__init__(f"No configuration setting is named {setting_name!r}.")


def documented_setting_names() -> "Sequence[str]":
    """Return the name of every setting that can be viewed or changed, in order."""
    return sorted(get_settings_metadata())


def _key_path_of(setting_name: str) -> "Sequence[str]":
    """Convert a colon-separated setting name into the sequence of keys it refers to."""
    if setting_name not in get_settings_metadata():
        raise UnknownSettingError(setting_name)

    return setting_name.split(SETTING_NAME_SEPARATOR)


def _read_as_yaml(raw_value: str) -> object:
    """Read the given text as though it had been written into the configuration file."""
    try:
        # NOTE: Deliberately the safe parser: the value comes from whoever ran the
        # command, & the round-trip parser used elsewhere can construct arbitrary
        # Python objects from a value that names them.
        return YAML(typ="safe", pure=True).load(raw_value)
    except YAMLError:
        return None


def parse_setting_value(setting_name: str, raw_value: str) -> object:
    """
    Convert the text a committee member typed into the value to write into the file.

    The text is read exactly as it would be if it had been written into the
    configuration file by hand, so that `true` becomes a boolean, `30` becomes a number,
    and `1h30m` remains the text of a duration.

    A setting declared to hold text is kept as text, so that a value which merely looks
    like a number (an organisation ID of `1234`, for example) is not written as one &
    then rejected for being the wrong type. Quoting such a value is still respected,
    so that `"1234"` means the same as `1234` rather than including the quotes.
    """
    PARSED_VALUE: Final[object] = _read_as_yaml(raw_value)

    if setting_metadata(setting_name).holds_text:
        return PARSED_VALUE if isinstance(PARSED_VALUE, str) else raw_value

    if isinstance(PARSED_VALUE, dict):
        # NOTE: A value holding a colon parses as a mapping, even though somebody typing
        # `Computer Science: Society` into a single setting meant it as plain text.
        return raw_value

    if PARSED_VALUE is None and raw_value.strip().lower() not in _NULL_LITERALS:
        # NOTE: A value beginning with `#` parses as a comment, & so as nothing at all,
        # as does a value that cannot be read as YAML at all.
        return raw_value

    return PARSED_VALUE


def _format_duration(duration: datetime.timedelta) -> str:
    """Render a length of time in the same format the configuration file holds it in."""
    remaining_seconds: float = duration.total_seconds()
    if remaining_seconds <= 0:
        return "0s"

    formatted_duration: str = ""

    unit_name: str
    seconds_within_unit: int
    for unit_name, seconds_within_unit in (("d", 86400), ("h", 3600), ("m", 60)):
        unit_count: int = int(remaining_seconds // seconds_within_unit)
        if unit_count:
            formatted_duration += f"{unit_count}{unit_name}"
            remaining_seconds -= unit_count * seconds_within_unit

    if remaining_seconds:
        formatted_duration += f"{remaining_seconds:g}s"

    return formatted_duration


def format_setting_value(value: object, *, secret: bool) -> str:
    """
    Render the value of a single setting into something readable.

    A secret value is never rendered, so that displaying a setting cannot reveal a
    credential to whoever can see the response.
    """
    if value is None:
        return UNSET_VALUE_DISPLAY

    if secret or isinstance(value, SecretStr):
        return REDACTED_VALUE_DISPLAY

    if isinstance(value, datetime.timedelta):
        return f"`{_format_duration(value)}`"

    if isinstance(value, tuple):
        return ", ".join(f"`{single_value}`" for single_value in value) or UNSET_VALUE_DISPLAY

    if isinstance(value, bool):
        return f"`{str(value).lower()}`"

    return f"`{value}`"


def _validated(document: SettingsDocument) -> SettingsDocument:
    """Return the given document, having checked that it holds a valid configuration."""
    validation_error: ValidationError
    try:
        SettingsSchema.model_validate(document.raw)
    except ValidationError as validation_error:
        raise SettingsValidationError(
            document.format_validation_error(validation_error)
        ) from validation_error

    return document


def validated_document_with_setting_set(setting_name: str, value: object) -> SettingsDocument:
    """
    Return the configuration file, holding the given value for the given setting.

    The file is read again rather than reusing the configuration already loaded, so that
    any change made to it by hand since then is kept rather than being overwritten.

    Nothing is written to disk: the returned document must be written by its caller.
    """
    KEY_PATH: Final[Sequence[str]] = _key_path_of(setting_name)

    document: SettingsDocument = SettingsDocument.load().copy()
    document.set_value(KEY_PATH, value)

    return _validated(document)


def validated_document_with_setting_removed(setting_name: str) -> SettingsDocument | None:
    """
    Return the configuration file, no longer holding the given setting.

    `None` is returned where the setting was not written within the file to begin with,
    because removing it would leave the file exactly as it already is.

    Nothing is written to disk: the returned document must be written by its caller.
    """
    KEY_PATH: Final[Sequence[str]] = _key_path_of(setting_name)

    document: SettingsDocument = SettingsDocument.load().copy()
    if not document.unset_value(KEY_PATH):
        return None

    return _validated(document)


def setting_metadata(setting_name: str) -> "ConfigSettingMetadata":
    """Return the metadata describing the given setting."""
    SETTINGS_METADATA: Final[Mapping[str, ConfigSettingMetadata]] = get_settings_metadata()

    if setting_name not in SETTINGS_METADATA:
        raise UnknownSettingError(setting_name)

    return SETTINGS_METADATA[setting_name]
