"""Custom exception classes related to configuration changes."""

from typing import TYPE_CHECKING, override

__all__: Sequence[str] = (
    "RestartRequiredDueToConfigChange",
    "ChangingSettingWithRequiredSiblingError",
)
from typed_classproperties import classproperty

from .base import BaseTeXBotError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet

__all__: "Sequence[str]" = ("ImproperlyConfiguredError", "RestartRequiredDueToConfigChange")


class ImproperlyConfiguredError(BaseTeXBotError, Exception):
    """Exception class to raise when environment variables are not correctly provided."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "One or more provided environment variable values are invalid."


class RestartRequiredDueToConfigChange(BaseTeXBotError, Exception):  # noqa: N818
    """Exception class to raise when a restart is required to apply config changes."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "TeX-Bot requires a restart to apply configuration changes."

    @override
    def __init__(
        self, message: str | None = None, changed_settings: "AbstractSet[str] | None" = None
    ) -> None:
        """Initialise an Exception to apply configuration changes."""
        self.changed_settings: AbstractSet[str] | None = changed_settings or set()

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
    def __init__(
        self, message: str | None = None, config_setting_name: str | None = None
    ) -> None:  # noqa: E501
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
