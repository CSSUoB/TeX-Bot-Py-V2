"""Custom exception classes related to configuration changes."""

from collections.abc import Sequence

__all__: Sequence[str] = ("BotRequiresRestartAfterConfigChange",)


from .base import BaseTeXBotError

from classproperties import classproperty


class BotRequiresRestartAfterConfigChange(BaseTeXBotError):
    """Exception class to raise to enforce handling of bot restarts after config changes."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "TeX-Bot requires a restart due to configuration changes."

    def __init__(self, message: str | None = None, changed_settings: set[str] | None = None) -> None:  # noqa: E501
        """Initialize a ValueError exception for a non-existent user ID."""
        self.changed_settings: set[str] | None = changed_settings

        super().__init__(message)
