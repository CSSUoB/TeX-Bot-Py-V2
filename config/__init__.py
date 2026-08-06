"""
Contains settings values and import & setup functions.

Settings values are loaded from the `tex-bot-deployment.yaml` deployment configuration
file, validated against the schema declared within `config._schema`. These values
configure the functionality of TeX-Bot at run-time, and can be reloaded without
restarting TeX-Bot.
"""

import importlib
import logging
from typing import TYPE_CHECKING

from ._accessor import SettingsAccessor, SettingsNotLoadedError, SettingsValidationError
from ._document import (
    InvalidSettingsFileError,
    SettingsDocument,
    SettingsFileNotFoundError,
    get_settings_file_path,
)
from ._logging import apply_logging_settings
from ._messages import MessagesAccessor
from ._schema import ConfigSettingMetadata, get_settings_metadata

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = (
    "ConfigSettingMetadata",
    "InvalidSettingsFileError",
    "SettingsDocument",
    "SettingsFileNotFoundError",
    "SettingsNotLoadedError",
    "SettingsValidationError",
    "get_settings_file_path",
    "get_settings_metadata",
    "messages",
    "reload_settings",
    "run_setup",
    "settings",
)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

settings: "Final[SettingsAccessor]" = SettingsAccessor()

messages: "Final[MessagesAccessor]" = MessagesAccessor()


def reload_settings() -> "AbstractSet[str]":
    """
    Reload the deployment configuration file, applying any settings that have changed.

    Returns the set of settings key paths whose values have changed.

    The currently loaded configuration is left untouched if the file cannot be read or
    contains invalid settings.
    """
    CHANGED_SETTINGS: Final[AbstractSet[str]] = settings.reload()

    if any(changed_setting.startswith("logging:") for changed_setting in CHANGED_SETTINGS):
        apply_logging_settings(settings.logging)

    return CHANGED_SETTINGS


def run_setup() -> None:
    """Execute the setup functions required before TeX-Bot can be run."""
    reload_settings()

    messages.reload()

    logger.debug("Begin database setup")

    importlib.import_module("db")
    importlib.import_module("django.core.management").call_command("migrate")

    logger.debug("Database setup completed")
