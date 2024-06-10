"""Custom exception classes related to configuration changes."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "BotRequiresRestartAfterConfigChange",
    "ChangingSettingWithRequiredSiblingError",
)


from typing import override

from classproperties import classproperty

from .base import BaseTeXBotError


class BotRequiresRestartAfterConfigChange(BaseTeXBotError, Exception):
    """Exception class to raise to enforce handling of bot restarts after config changes."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "TeX-Bot requires a restart due to configuration changes."

    @override
    def __init__(self, message: str | None = None, changed_settings: set[str] | None = None) -> None:  # noqa: E501
        """Initialize a ValueError exception for a non-existent user ID."""
        self.changed_settings: set[str] | None = changed_settings

        super().__init__(message)


class ChangingSettingWithRequiredSiblingError(BaseTeXBotError, ValueError):
    """Exception class for when a setting cannot be changed because of required siblings."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return (
            "The given setting cannot be changed "
            "because it has one or more required sibling settings that must be set first."
        )

    @override
    def __init__(self, message: str | None = None, config_setting_name: str | None = None) -> None:  # noqa: E501
        self.config_setting_name: str | None = config_setting_name

        super().__init__(
            message
            or (
                f"Cannot assign value to config setting '{config_setting_name}' "
                f"because it has one or more required sibling settings that must be set first."
                if config_setting_name
                else message
            )  # noqa: COM812
        )
