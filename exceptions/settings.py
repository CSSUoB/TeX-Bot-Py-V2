"""Custom exception classes related to reading & changing the deployment configuration."""

from typing import TYPE_CHECKING, override

from typed_classproperties import classproperty

from .base import BaseTeXBotError
from .config_changes import ImproperlyConfiguredError

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "InvalidSettingsFileError",
    "SettingsFileChangedError",
    "SettingsFileNotFoundError",
    "SettingsNotLoadedError",
    "SettingsValidationError",
    "UnknownSettingError",
)


class SettingsFileNotFoundError(ImproperlyConfiguredError):
    """Exception class to raise when no deployment configuration file could be located."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "No deployment configuration file could be located."


class InvalidSettingsFileError(ImproperlyConfiguredError):
    """Exception class to raise when the deployment configuration file could not be read."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "The deployment configuration file could not be read."


class SettingsNotLoadedError(BaseTeXBotError, Exception):
    """Exception class to raise when configuration is accessed before it has been loaded."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "Configuration cannot be accessed before it has been loaded."


class SettingsValidationError(ImproperlyConfiguredError):
    """Exception class to raise when the configuration file contains invalid settings."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "The configuration file contains invalid settings."


class UnknownSettingError(BaseTeXBotError, Exception):
    """Exception class to raise when a setting that the schema does not declare is named."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "No configuration setting is named that."

    @override
    def __init__(self, setting_name: str) -> None:
        """Initialise a new UnknownSettingError for the given setting name."""
        self.setting_name: str = setting_name

        super().__init__(f"No configuration setting is named {setting_name!r}.")


class SettingsFileChangedError(BaseTeXBotError, Exception):
    """Exception class to raise when the configuration file has been edited by hand."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "The configuration file has been changed since TeX-Bot last loaded it."
