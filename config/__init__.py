"""
Contains settings values and import & setup functions.

Settings values are loaded from the `tex-bot-deployment.yaml` deployment configuration
file, validated against the schema declared within `config._schema`. These values
configure the functionality of TeX-Bot at run-time, and can be reloaded without
restarting TeX-Bot.
"""

import importlib
import logging
from typing import TYPE_CHECKING, NamedTuple

from ._accessor import SettingsAccessor, SettingsNotLoadedError, SettingsValidationError
from ._document import (
    InvalidSettingsFileError,
    SettingsDocument,
    SettingsFileNotFoundError,
    get_settings_file_path,
)
from ._editor import (
    SETTING_NAME_SEPARATOR,
    SettingsFileChangedError,
    UnknownSettingError,
    documented_setting_names,
    format_setting_value,
    parse_setting_value,
    setting_metadata,
    validated_document_with_setting_removed,
    validated_document_with_setting_set,
)
from ._logging import apply_logging_settings
from ._messages import MessagesAccessor
from ._schema import ConfigSettingMetadata, get_settings_metadata

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = (
    "SETTING_NAME_SEPARATOR",
    "ConfigReloadResult",
    "ConfigSettingMetadata",
    "InvalidSettingsFileError",
    "SettingsDocument",
    "SettingsFileChangedError",
    "SettingsFileNotFoundError",
    "SettingsNotLoadedError",
    "SettingsValidationError",
    "UnknownSettingError",
    "documented_setting_names",
    "format_setting_value",
    "get_settings_file_path",
    "get_settings_metadata",
    "messages",
    "reload_settings",
    "run_setup",
    "set_setting",
    "setting_metadata",
    "settings",
    "unset_setting",
)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

settings: "Final[SettingsAccessor]" = SettingsAccessor()

messages: "Final[MessagesAccessor]" = MessagesAccessor()


class ConfigReloadResult(NamedTuple):
    """The outcome of reloading the deployment configuration file."""

    changed_settings: "AbstractSet[str]"
    restart_required_settings: "AbstractSet[str]"


def reload_settings() -> ConfigReloadResult:
    """
    Reload the deployment configuration file, applying any settings that have changed.

    Returns the settings key paths whose values have changed, along with the subset of
    those that cannot take effect until TeX-Bot is restarted.

    The currently loaded configuration is left untouched if the file cannot be read or
    contains invalid settings.
    """
    CHANGED_SETTINGS: Final[AbstractSet[str]] = settings.reload()

    if any(changed_setting.startswith("logging:") for changed_setting in CHANGED_SETTINGS):
        apply_logging_settings(settings.logging)

    SETTINGS_METADATA: Final[Mapping[str, ConfigSettingMetadata]] = get_settings_metadata()

    return ConfigReloadResult(
        changed_settings=CHANGED_SETTINGS,
        # NOTE: Read from the schema itself, rather than tracked separately, so that the
        # two cannot disagree about which settings need a restart.
        restart_required_settings=frozenset(
            changed_setting
            for changed_setting in CHANGED_SETTINGS
            if changed_setting in SETTINGS_METADATA
            and SETTINGS_METADATA[changed_setting].requires_restart
        ),
    )


def _loaded_document() -> "SettingsDocument | None":
    """Return the configuration document currently loaded, if any configuration has been."""
    return settings.document if settings.is_loaded else None


def set_setting(setting_name: str, raw_value: str) -> ConfigReloadResult:
    """
    Change a single setting within the configuration file, then apply the change.

    The new value is validated before the file is written, so a value that would be
    rejected leaves both the file & the running configuration exactly as they were.

    Changing a file that has been edited by hand since it was last loaded is refused,
    so that a change is only ever made against the configuration TeX-Bot is running.

    Returns the settings that changed as a result, along with the subset of those that
    cannot take effect until TeX-Bot is restarted.
    """
    UPDATED_DOCUMENT: Final[SettingsDocument] = validated_document_with_setting_set(
        setting_name, parse_setting_value(setting_name, raw_value), _loaded_document()
    )

    UPDATED_DOCUMENT.write()

    return reload_settings()


def unset_setting(setting_name: str) -> ConfigReloadResult | None:
    """
    Remove a single setting from the configuration file, then apply its removal.

    The setting returns to its default value. `None` is returned where the setting was
    not written within the file to begin with, so nothing needed to be removed.

    Removing a setting that is required leaves the file untouched, because the
    configuration that removing it would produce is not valid. Removing a setting from a
    file that has been edited by hand since it was last loaded is likewise refused.
    """
    UPDATED_DOCUMENT: Final[SettingsDocument | None] = validated_document_with_setting_removed(
        setting_name, _loaded_document()
    )

    if UPDATED_DOCUMENT is None:
        return None

    UPDATED_DOCUMENT.write()

    return reload_settings()


def run_setup() -> None:
    """Execute the setup functions required before TeX-Bot can be run."""
    reload_settings()

    messages.reload()

    logger.debug("Begin database setup")

    importlib.import_module("db")
    importlib.import_module("django.core.management").call_command("migrate")

    logger.debug("Database setup completed")
