"""Custom exception classes related to configuration changes."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "ImproperlyConfiguredError",
    "RestartRequiredDueToConfigChange",
)


from collections.abc import Set
from typing import override

from classproperties import classproperty

from .base import BaseTeXBotError


class ImproperlyConfiguredError(BaseTeXBotError, Exception):
    """Exception class to raise when environment variables are not correctly provided."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "One or more provided environment variable values are invalid."


class RestartRequiredDueToConfigChange(BaseTeXBotError, Exception):  # noqa: N818
    """Exception class to raise when a restart is required to apply config changes."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "TeX-Bot requires a restart to apply configuration changes."

    @override
    def __init__(self, message: str | None = None, changed_settings: Set[str] | None = None) -> None:  # noqa: E501
        """Initialise an Exception to apply configuration changes."""
        self.changed_settings: Set[str] | None = (
            changed_settings if changed_settings else set()
        )

        super().__init__(message)
