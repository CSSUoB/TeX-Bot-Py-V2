"""Custom exception classes related to configuration changes."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "RestartRequiredDueToConfigChange",
    "ChangingSettingWithRequiredSiblingError",
)


from collections.abc import Set
from typing import override

from classproperties import classproperty

from .base import BaseTeXBotError


class RestartRequiredDueToConfigChange(BaseTeXBotError, Exception):
    """Exception class to raise when a restart is required to apply config changes."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "TeX-Bot requires a restart to apply configuration changes."

    @override
    def __init__(self, message: str | None = None, changed_settings: Set[str] | None = None) -> None:  # noqa: E501
        """Initialise an Exception to apply configuration changes."""
        self.changed_settings: Set[str] | None = changed_settings if changed_settings else set()

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
