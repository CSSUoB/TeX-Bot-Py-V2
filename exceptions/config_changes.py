"""Custom exception classes related to configuration changes."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "ImproperlyConfiguredError",
    "BotRequiresRestartAfterConfigChange",
)


class ImproperlyConfiguredError(Exception):
    """Exception class to raise when environment variables are not correctly provided."""

class BotRequiresRestartAfterConfigChange(Exception):
    """Exception class to raise when the bot requires a reboot to apply changes."""
