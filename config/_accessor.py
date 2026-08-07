"""
Runtime access to the validated deployment configuration.

Holds the currently-loaded configuration as a single immutable snapshot, replaced
wholesale whenever the configuration is reloaded. Because a reload swaps one reference
rather than mutating settings individually, no reader can ever observe a partially
applied configuration, even if reloading fails partway through.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

from ._document import InvalidSettingsFileError, SettingsDocument, SettingsFileNotFoundError
from ._schema import SettingsSchema, nested_settings_model_of, setting_names_within

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from collections.abc import Set as AbstractSet
    from pathlib import Path
    from typing import Final

    from pydantic.fields import FieldInfo

    from ._schema import (
        CommandsSettings,
        CommunityGroupSettings,
        DiscordSettings,
        LoggingSettings,
        RemindersSettings,
    )


__all__: "Sequence[str]" = (
    "SettingsAccessor",
    "SettingsNotLoadedError",
    "SettingsValidationError",
)


class SettingsNotLoadedError(Exception):
    """Exception class to raise when configuration is accessed before it has been loaded."""

    def __init__(self, message: str | None = None) -> None:
        """Initialise a new SettingsNotLoadedError with the given message."""
        super().__init__(
            message or "Configuration cannot be accessed before it has been loaded."
        )


class SettingsValidationError(Exception):
    """Exception class to raise when the configuration file contains invalid settings."""


@dataclass(frozen=True, slots=True)
class _LoadedSettings:
    """
    A validated configuration snapshot, paired with the document it was parsed from.

    Holding both within a single frozen object allows a reload to replace them together,
    by rebinding one reference, so the two can never disagree with one another.
    """

    snapshot: SettingsSchema
    document: SettingsDocument


_MISSING: "Final[object]" = object()


def _flatten_settings(model: BaseModel, prefix: str = "") -> "Mapping[str, object]":
    """
    Flatten a settings model into a mapping of colon-separated key paths to values.

    Nested sections are expanded recursively, so that
    `{"discord": {"bot-token": ...}}` becomes `{"discord:bot-token": ...}`,
    matching the key paths used by the `/config` command.
    """
    flattened_settings: dict[str, object] = {}

    field_name: str
    field: FieldInfo
    for field_name, field in type(model).model_fields.items():
        value: object = getattr(model, field_name)
        KEY_PATH: str = f"{prefix}{field_name.replace('_', '-')}"

        if isinstance(value, BaseModel):
            flattened_settings.update(_flatten_settings(value, prefix=f"{KEY_PATH}:"))
            continue

        NESTED_MODEL: type[BaseModel] | None = nested_settings_model_of(field)
        if NESTED_MODEL is not None:
            # NOTE: An optional section left out of the file holds no value of its own;
            # every setting within it is simply unset. Naming those settings, rather than
            # the section holding them, keeps every key path reported by a reload one that
            # the `/config` command recognises.
            flattened_settings.update(
                dict.fromkeys(setting_names_within(NESTED_MODEL, prefix=f"{KEY_PATH}:"))
            )
            continue

        flattened_settings[KEY_PATH] = value

    return flattened_settings


class SettingsAccessor:
    """
    Provides access to the validated configuration settings.

    Settings are accessed by section, as attributes
    (for example: `settings.discord.bot_token`).
    """

    def __init__(self) -> None:
        """Initialise an accessor holding no configuration until it is first loaded."""
        self._loaded: _LoadedSettings | None = None

    @property
    def is_loaded(self) -> bool:
        """Whether any configuration has been loaded yet."""
        return self._loaded is not None

    @property
    def _current(self) -> _LoadedSettings:
        """The currently-loaded configuration, raising if none has been loaded yet."""
        if self._loaded is None:
            raise SettingsNotLoadedError

        return self._loaded

    @property
    def file_path(self) -> "Path":
        """The location of the configuration file that is currently loaded."""
        return self._current.document.file_path

    @property
    def document(self) -> SettingsDocument:
        """
        The document that the currently-loaded configuration was parsed from.

        Used to rewrite individual settings while retaining the comments & formatting
        of the file that a human wrote.
        """
        return self._current.document

    def file_has_changed(self) -> bool:
        """
        Whether the configuration file differs from the configuration loaded from it.

        Compared as the documents parse to, rather than as raw text, so that a file
        rewritten with different line endings is not mistaken for one that was edited.

        A file that can no longer be read at all is reported as changed, rather than
        raising: it certainly no longer holds the configuration that was loaded from it,
        & saying so is what allows the caller to explain that instead of failing.
        """
        if self._loaded is None:
            return False

        try:
            return SettingsDocument.load(self.file_path).dump() != self._loaded.document.dump()
        except (SettingsFileNotFoundError, InvalidSettingsFileError, OSError):
            return True

    def reload(self, file_path: "Path | None" = None) -> "AbstractSet[str]":
        """
        Load the configuration file, replacing any previously loaded configuration.

        Returns the set of settings key paths whose values differ from those previously
        loaded. Every setting is reported as changed upon the very first load.

        The previously loaded configuration is left untouched if the file cannot be read
        or contains invalid settings, so that a bad edit cannot take a running bot down.
        """
        document: SettingsDocument = SettingsDocument.load(file_path)

        validation_error: ValidationError
        try:
            snapshot: SettingsSchema = SettingsSchema.model_validate(document.raw)
        except ValidationError as validation_error:
            raise SettingsValidationError(
                document.format_validation_error(validation_error)
            ) from validation_error

        PREVIOUS_SETTINGS: Final[Mapping[str, object]] = (
            {} if self._loaded is None else _flatten_settings(self._loaded.snapshot)
        )
        NEW_SETTINGS: Final[Mapping[str, object]] = _flatten_settings(snapshot)

        # NOTE: Rebinding this single reference is what makes a reload atomic: every
        # reader either sees the whole of the previous configuration, or the whole of the
        # new one. Both the validation above & the file reading before it can raise, and
        # neither will have left the currently-loaded configuration partially updated.
        self._loaded = _LoadedSettings(snapshot=snapshot, document=document)

        return {
            key_path
            for key_path in (PREVIOUS_SETTINGS.keys() | NEW_SETTINGS.keys())
            if PREVIOUS_SETTINGS.get(key_path, _MISSING)
            != NEW_SETTINGS.get(key_path, _MISSING)
        }

    def as_flat_mapping(self) -> "Mapping[str, object]":
        """
        Return every loaded setting, as a mapping of colon-separated key paths to values.

        Used by the `/config` command to view settings by name.
        """
        return _flatten_settings(self._current.snapshot)

    @property
    def logging(self) -> "LoggingSettings":
        """Settings controlling every logging destination TeX-Bot can write to."""
        return self._current.snapshot.logging

    @property
    def discord(self) -> "DiscordSettings":
        """Settings describing how TeX-Bot connects to Discord."""
        return self._current.snapshot.discord

    @property
    def community_group(self) -> "CommunityGroupSettings":
        """Settings describing the community group that TeX-Bot is deployed for."""
        return self._current.snapshot.community_group

    @property
    def commands(self) -> "CommandsSettings":
        """Settings controlling the behaviour of TeX-Bot's individual commands."""
        return self._current.snapshot.commands

    @property
    def reminders(self) -> "RemindersSettings":
        """Settings controlling every kind of reminder that TeX-Bot can send."""
        return self._current.snapshot.reminders

    @property
    def auto_add_committee_to_threads(self) -> bool:
        """Whether committee members are automatically added to newly created threads."""
        return self._current.snapshot.auto_add_committee_to_threads
