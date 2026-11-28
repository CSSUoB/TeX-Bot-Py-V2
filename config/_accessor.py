"""
Runtime access to the validated deployment configuration.

Holds the currently-loaded configuration as a single immutable snapshot, replaced
wholesale whenever the configuration is reloaded. Because a reload swaps one reference
rather than mutating settings individually, no reader can ever observe a partially
applied configuration, even if reloading fails partway through.

A setting that requires a restart keeps the value TeX-Bot started with, however many
times the configuration is reloaded. The value written within the file is held alongside
it, & takes effect once TeX-Bot is restarted.
"""

from typing import TYPE_CHECKING, override

from pydantic import BaseModel, ValidationError

from exceptions import (
    InvalidSettingsFileError,
    SettingsFileNotFoundError,
    SettingsNotLoadedError,
    SettingsValidationError,
)

from ._document import SettingsDocument
from ._schema import (
    SettingsSchema,
    get_settings_metadata,
    nested_settings_model_of,
    setting_names_within,
)

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


__all__: Sequence[str] = ("SettingsAccessor",)


class _LoadedSettings:
    """
    A validated configuration snapshot, paired with the document it was parsed from.

    Holding both within a single immutable object allows a reload to replace them together,
    by rebinding one reference, so the two can never disagree with one another.
    """

    @override
    def __init__(
        self,
        snapshot: SettingsSchema,
        document: SettingsDocument,
        running_snapshot: SettingsSchema,
    ) -> None:
        """Initialise a snapshot paired with the document it was parsed from."""
        self._snapshot: SettingsSchema = snapshot
        self._document: SettingsDocument = document
        self._running_snapshot: SettingsSchema = running_snapshot

    @property
    def snapshot(self) -> SettingsSchema:
        """The validated settings parsed from the document."""
        return self._snapshot

    @property
    def document(self) -> SettingsDocument:
        """The parsed document that the snapshot was loaded from."""
        return self._document

    @property
    def running_snapshot(self) -> SettingsSchema:
        """
        The settings TeX-Bot is running with.

        The same as the snapshot parsed from the document, except that every setting
        requiring a restart holds the value TeX-Bot started with.
        """
        return self._running_snapshot


_MISSING: Final[object] = object()


def flatten_settings(model: BaseModel, prefix: str = "") -> Mapping[str, object]:
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
            flattened_settings.update(flatten_settings(value, prefix=f"{KEY_PATH}:"))
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


def _setting_section(model: BaseModel, field_name: str) -> BaseModel:
    SECTION: Final[object] = getattr(model, field_name)

    if not isinstance(SECTION, BaseModel):
        NOT_A_SECTION_MESSAGE: Final[str] = (
            f"{field_name!r} does not hold a section of settings, "
            "so a setting cannot be found within it."
        )
        raise TypeError(NOT_A_SECTION_MESSAGE)

    return SECTION


def _setting_value(model: BaseModel, field_names: Sequence[str]) -> object:
    if len(field_names) == 1:
        return getattr(model, field_names[0])

    return _setting_value(_setting_section(model, field_names[0]), field_names[1:])


def _with_setting_value[T: BaseModel](
    model: T, field_names: Sequence[str], value: object
) -> T:
    """Return a copy of the given settings model, with a single setting replaced."""
    if len(field_names) == 1:
        return model.model_copy(update={field_names[0]: value})

    return model.model_copy(
        update={
            field_names[0]: _with_setting_value(
                _setting_section(model, field_names[0]), field_names[1:], value
            )
        }
    )


def _restart_setting_key_paths() -> AbstractSet[str]:
    """Return the key path of every setting that requires a restart to take effect."""
    return {
        key_path
        for key_path, setting_metadata in get_settings_metadata().items()
        if setting_metadata.requires_restart
    }


def _with_start_up_values_of_restart_settings(
    snapshot: SettingsSchema, start_up_snapshot: SettingsSchema
) -> SettingsSchema:
    """
    Return a copy of the given snapshot, holding the start-up value of every restart setting.

    A setting requiring a restart is one that TeX-Bot reads only as it starts up, so
    letting a reload replace it would leave the parts of TeX-Bot that read it once out
    of step with those that read it on every use.
    """
    running_snapshot: SettingsSchema = snapshot

    key_path: str
    for key_path in _restart_setting_key_paths():
        FIELD_NAMES: Sequence[str] = tuple(
            key_part.replace("-", "_") for key_part in key_path.split(":")
        )
        running_snapshot = _with_setting_value(
            running_snapshot, FIELD_NAMES, _setting_value(start_up_snapshot, FIELD_NAMES)
        )

    return running_snapshot


class SettingsAccessor:
    """
    Provides access to the validated configuration settings.

    Settings are accessed by section, as attributes
    (for example: `settings.discord.bot_token`).
    """

    @override
    def __init__(self) -> None:
        """Initialise an accessor holding no configuration until it is first loaded."""
        self._loaded: _LoadedSettings | None = None
        self._start_up_snapshot: SettingsSchema | None = None

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
    def file_path(self) -> Path:
        """The location of the configuration file that is currently loaded."""
        return self._current.document.file_path

    @property
    def document(self) -> SettingsDocument:
        """
        The document that the currently-loaded configuration was parsed from.

        Used to rewrite individual settings while keeping the order & quoting of the file
        that a human wrote.
        """
        return self._current.document

    def file_has_changed(self) -> bool:
        """
        Whether the configuration file differs from the configuration loaded from it.

        Compared as the documents parse to, rather than as raw text, so that a file
        rewritten with different line endings is not mistaken for one that was edited.
        Comments are not compared, because TeX-Bot does not write them back.

        A file that can no longer be read at all is reported as changed, rather than
        raising: it certainly no longer holds the configuration that was loaded from it,
        & saying so is what allows the caller to explain that instead of failing.
        """
        if self._loaded is None:
            return False

        try:
            return SettingsDocument.load(self.file_path).dump() != self._loaded.document.dump()
        except SettingsFileNotFoundError, InvalidSettingsFileError, OSError:
            return True

    def reload(self, file_path: Path | None = None) -> AbstractSet[str]:
        """
        Load the configuration file, replacing any previously loaded configuration.

        Returns the set of settings key paths whose values differ from those previously
        loaded. Every setting is reported as changed upon the very first load.

        The previously loaded configuration is left untouched if the file cannot be read
        or contains invalid settings, so that a bad edit cannot take a running bot down.

        The very first configuration loaded is the one TeX-Bot starts with, so every
        setting requiring a restart keeps its value from that load until TeX-Bot restarts.
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
            {} if self._loaded is None else flatten_settings(self._loaded.snapshot)
        )
        NEW_SETTINGS: Final[Mapping[str, object]] = flatten_settings(snapshot)

        if self._start_up_snapshot is None:
            self._start_up_snapshot = snapshot

        # NOTE: Rebinding this single reference is what makes a reload atomic: every
        # reader either sees the whole of the previous configuration, or the whole of the
        # new one. Both the validation above & the file reading before it can raise, and
        # neither will have left the currently-loaded configuration partially updated.
        self._loaded = _LoadedSettings(
            snapshot=snapshot,
            document=document,
            running_snapshot=_with_start_up_values_of_restart_settings(
                snapshot, self._start_up_snapshot
            ),
        )

        return {
            key_path
            for key_path in (PREVIOUS_SETTINGS.keys() | NEW_SETTINGS.keys())
            if PREVIOUS_SETTINGS.get(key_path, _MISSING)
            != NEW_SETTINGS.get(key_path, _MISSING)
        }

    def as_flat_mapping(self) -> Mapping[str, object]:
        """
        Return every running setting, as a mapping of colon-separated key paths to values.

        Used by the `/config` command to view settings by name. A setting requiring a
        restart is given the value TeX-Bot started with, which is the one in use.
        """
        return flatten_settings(self._current.running_snapshot)

    def as_flat_file_mapping(self) -> Mapping[str, object]:
        """
        Return every loaded setting, with the values held by the file when last loaded.

        Unlike `as_flat_mapping()`, this includes the new value of any setting that will
        not take effect until TeX-Bot is restarted.
        """
        return flatten_settings(self._current.snapshot)

    @property
    def values_awaiting_restart(self) -> Mapping[str, object]:
        """
        Every setting whose loaded value will not take effect until TeX-Bot is restarted.

        Each is mapped to the value held by the file, which differs from the value that
        TeX-Bot is running with.
        """
        RUNNING_SETTINGS: Final[Mapping[str, object]] = self.as_flat_mapping()

        return {
            key_path: file_value
            for key_path, file_value in self.as_flat_file_mapping().items()
            if file_value != RUNNING_SETTINGS.get(key_path, _MISSING)
        }

    @property
    def logging(self) -> LoggingSettings:
        """Settings controlling every logging destination TeX-Bot can write to."""
        return self._current.running_snapshot.logging

    @property
    def discord(self) -> DiscordSettings:
        """Settings describing how TeX-Bot connects to Discord."""
        return self._current.running_snapshot.discord

    @property
    def community_group(self) -> CommunityGroupSettings:
        """Settings describing the community group that TeX-Bot is deployed for."""
        return self._current.running_snapshot.community_group

    @property
    def commands(self) -> CommandsSettings:
        """Settings controlling the behaviour of TeX-Bot's individual commands."""
        return self._current.running_snapshot.commands

    @property
    def reminders(self) -> RemindersSettings:
        """Settings controlling every kind of reminder that TeX-Bot can send."""
        return self._current.running_snapshot.reminders

    @property
    def auto_add_committee_to_threads(self) -> bool:
        """Whether committee members are automatically added to newly created threads."""
        return self._current.running_snapshot.auto_add_committee_to_threads
