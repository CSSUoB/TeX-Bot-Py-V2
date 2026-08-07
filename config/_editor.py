"""
Changing individual settings within the deployment configuration file.

Every change is applied to the configuration file read afresh, & validated in full,
before anything is written, so that a mistaken value can never leave TeX-Bot holding a
configuration file it would refuse to load. A file that has been changed by hand since
it was last loaded is refused outright, rather than merged into, so that every change
is made against the configuration that TeX-Bot is actually running.

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

from exceptions import (
    InvalidSettingsFileError,
    SettingsFileChangedError,
    SettingsFileNotFoundError,
    SettingsValidationError,
    UnknownSettingError,
)

from ._accessor import flatten_settings
from ._document import SettingsDocument
from ._schema import SettingsSchema, get_settings_metadata

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path
    from typing import Final

    from ._schema import ConfigSettingMetadata


__all__: "Sequence[str]" = (
    "SETTING_NAME_SEPARATOR",
    "documented_setting_names",
    "format_file_difference",
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


def _snapshot_of(document: SettingsDocument) -> SettingsSchema:
    """Return the settings held by the given document, refusing it if they are invalid."""
    validation_error: ValidationError
    try:
        return SettingsSchema.model_validate(document.raw)
    except ValidationError as validation_error:
        raise SettingsValidationError(
            document.format_validation_error(validation_error)
        ) from validation_error


def _validated(document: SettingsDocument) -> SettingsDocument:
    """Return the given document, having checked that it holds a valid configuration."""
    _snapshot_of(document)

    return document


def format_file_difference(
    setting_name: str,
    running_value: object,
    *,
    secret: bool,
    file_path: "Path | None" = None,
) -> str:
    """
    Describe how the configuration file's value for a setting differs from the running one.

    Intended to be shown alongside the value TeX-Bot is running, once the file is known
    to have been edited since it was last loaded, so that whoever is looking at a setting
    can see what reloading would change it to rather than only being told to reload.

    The file compared against is the one the running configuration was loaded from, which
    must be given explicitly: it is not necessarily the one that would be located afresh.
    """
    file_error: Exception
    try:
        FILE_VALUES: Final[Mapping[str, object]] = flatten_settings(
            _snapshot_of(SettingsDocument.load(file_path))
        )
    except (
        SettingsValidationError,
        SettingsFileNotFoundError,
        InvalidSettingsFileError,
        OSError,
    ) as file_error:
        return (
            "\n\n:warning: The configuration file has been edited since TeX-Bot last "
            "loaded it, but cannot be loaded as it currently stands:\n"
            f"```\n{file_error}\n```"
        )

    # NOTE: A setting within a section that has been left out of the file entirely has no
    # entry of its own, & is simply unset.
    FILE_VALUE: Final[object] = FILE_VALUES.get(setting_name)

    if running_value == FILE_VALUE:
        return (
            "\n\n:information_source: The configuration file has been edited since "
            "TeX-Bot last loaded it, though not this setting. "
            "Run `/config reload` to apply those edits."
        )

    if secret:
        return (
            "\n\n:warning: The configuration file holds a different value for this "
            "setting, which TeX-Bot has not loaded. "
            "Run `/config reload` to apply that edit."
        )

    return (
        f"\n\n:warning: The configuration file has been edited since TeX-Bot last "
        f"loaded it:\n"
        f"- currently running: {format_setting_value(running_value, secret=secret)}\n"
        f"- within the file: {format_setting_value(FILE_VALUE, secret=secret)}\n"
        f"Run `/config reload` to apply that edit."
    )


def _read_unchanged_file(loaded_document: SettingsDocument | None) -> SettingsDocument:
    """
    Read the configuration file again, refusing it if it no longer matches what is loaded.

    A change made by hand is refused rather than merged into, so that changing one
    setting cannot silently apply somebody else's unrelated edits alongside it, nor
    report that TeX-Bot must be restarted for a setting its author never touched.

    The file read is the one the given document was loaded from, so that a change is
    always made to the file TeX-Bot is running, rather than to whichever file would be
    located afresh.
    """
    document: SettingsDocument = SettingsDocument.load(
        None if loaded_document is None else loaded_document.file_path
    )

    # NOTE: Nothing has been loaded for the file to have diverged from while TeX-Bot is
    # still starting up, so there is nothing to compare it against.
    if loaded_document is not None and document.dump() != loaded_document.dump():
        raise SettingsFileChangedError

    return document


def validated_document_with_setting_set(
    setting_name: str, value: object, loaded_document: SettingsDocument | None = None
) -> SettingsDocument:
    """
    Return the configuration file, holding the given value for the given setting.

    The file is refused if it has been changed by hand since it was last loaded, so that
    a change is only ever applied to the configuration TeX-Bot is actually running.

    Nothing is written to disk: the returned document must be written by its caller.
    """
    KEY_PATH: Final[Sequence[str]] = _key_path_of(setting_name)

    document: SettingsDocument = _read_unchanged_file(loaded_document)
    document.set_value(KEY_PATH, value)

    return _validated(document)


def validated_document_with_setting_removed(
    setting_name: str, loaded_document: SettingsDocument | None = None
) -> SettingsDocument | None:
    """
    Return the configuration file, no longer holding the given setting.

    `None` is returned where the setting was not written within the file to begin with,
    because removing it would leave the file exactly as it already is.

    The file is refused if it has been changed by hand since it was last loaded.

    Nothing is written to disk: the returned document must be written by its caller.
    """
    KEY_PATH: Final[Sequence[str]] = _key_path_of(setting_name)

    document: SettingsDocument = _read_unchanged_file(loaded_document)
    if not document.unset_value(KEY_PATH):
        return None

    return _validated(document)


def setting_metadata(setting_name: str) -> "ConfigSettingMetadata":
    """Return the metadata describing the given setting."""
    SETTINGS_METADATA: Final[Mapping[str, ConfigSettingMetadata]] = get_settings_metadata()

    if setting_name not in SETTINGS_METADATA:
        raise UnknownSettingError(setting_name)

    return SETTINGS_METADATA[setting_name]
