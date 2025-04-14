"""Custom exception classes related to configuration changes."""

from typing import TYPE_CHECKING, override

from typed_classproperties import classproperty

from .base import BaseTeXBotError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet

__all__: "Sequence[str]" = (
    "ImproperlyConfiguredError",
    "RestartRequiredDueToConfigChange",
)


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
        self.changed_settings: AbstractSet[str] | None = (
            changed_settings if changed_settings else set()
        )

        super().__init__(message)
