"""
Application of the logging configuration held within the settings.

Logging is set up from the loaded settings rather than read directly from the
environment, so that changing a log level within the configuration file takes effect
upon the next reload without restarting TeX-Bot.
"""

import logging
from typing import TYPE_CHECKING

from discord_logging.handler import DiscordHandler

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Handler, Logger
    from typing import Final

    from ._schema import (
        DiscordAPILoggingSettings,
        DiscordChannelLoggingSettings,
        LoggingSettings,
    )


__all__: "Sequence[str]" = ("DISCORD_LOGGER_NAME", "LOGGER_NAME", "apply_logging_settings")


# NOTE: These hold the *names* of the loggers to retrieve, rather than the loggers
# themselves, so `Final[str]` is the correct annotation despite what CAR201 infers
# from the variable names.
LOGGER_NAME: "Final[str]" = "TeX-Bot"  # noqa: CAR201

DISCORD_LOGGER_NAME: "Final[str]" = "discord"  # noqa: CAR201

DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME: "Final[str]" = "TeX-Bot"

logger: "Final[Logger]" = logging.getLogger(LOGGER_NAME)

discord_logger: "Final[Logger]" = logging.getLogger(DISCORD_LOGGER_NAME)


def _remove_handlers_of_type(
    target_logger: "Logger", handler_type: type, *, excluding: type | None = None
) -> None:
    """
    Remove every handler of the given type from the given logger.

    A subtype of that type may be excluded, because the logging module's own handler
    hierarchy does not match the destinations they write to: `FileHandler` subclasses
    `StreamHandler`, so removing every stream handler would otherwise also remove the
    file handler that a different destination's settings are responsible for.
    """
    existing_handler: Handler
    for existing_handler in tuple(target_logger.handlers):
        HANDLER_IS_EXCLUDED: bool = excluding is not None and isinstance(
            existing_handler, excluding
        )
        if isinstance(existing_handler, handler_type) and not HANDLER_IS_EXCLUDED:
            target_logger.removeHandler(existing_handler)
            existing_handler.close()


def _apply_console_logging_settings(logging_settings: "LoggingSettings") -> None:
    """Set up logging to the console output stream."""
    # NOTE: Handlers are replaced rather than reconfigured in place, so that applying
    # settings repeatedly (upon every reload) cannot accumulate duplicate handlers.
    _remove_handlers_of_type(logger, logging.StreamHandler, excluding=logging.FileHandler)

    console_logging_handler: Handler = logging.StreamHandler()
    console_logging_handler.setFormatter(
        logging.Formatter("{asctime} | {name} | {levelname:^8} - {message}", style="{")
    )

    logger.setLevel(logging_settings.console.log_level)
    logger.addHandler(console_logging_handler)
    logger.propagate = False


def _apply_discord_channel_logging_settings(logging_settings: "LoggingSettings") -> None:
    """Set up relaying of error logs to a Discord log channel."""
    _remove_handlers_of_type(logger, DiscordHandler)

    DISCORD_CHANNEL_LOGGING_SETTINGS: Final[DiscordChannelLoggingSettings | None] = (
        logging_settings.discord_channel
    )
    if DISCORD_CHANNEL_LOGGING_SETTINGS is None:
        logger.debug(
            "No Discord log-channel webhook-URL was set, "
            "so error logs will not be sent to a Discord log-channel."
        )
        return

    discord_channel_logging_handler: Handler = DiscordHandler(
        DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME,
        str(DISCORD_CHANNEL_LOGGING_SETTINGS.webhook_url),
    )
    discord_channel_logging_handler.setLevel(DISCORD_CHANNEL_LOGGING_SETTINGS.log_level)
    discord_channel_logging_handler.setFormatter(
        logging.Formatter("{levelname} | {message}", style="{")
    )

    logger.addHandler(discord_channel_logging_handler)


def _apply_discord_api_logging_settings(logging_settings: "LoggingSettings") -> None:
    """Set up recording of the logs emitted by the Discord API wrapper."""
    _remove_handlers_of_type(discord_logger, logging.FileHandler)

    DISCORD_API_LOGGING_SETTINGS: Final[DiscordAPILoggingSettings] = (
        logging_settings.discord_api
    )
    if not DISCORD_API_LOGGING_SETTINGS.enabled:
        # NOTE: The level is restored alongside the handler, so that disabling these logs
        # after they have been enabled leaves the Discord API logger exactly as it began.
        # Leaving a previously configured level in place would otherwise send every record
        # meeting it to the root logger, now that propagation has been turned back on.
        discord_logger.setLevel(logging.NOTSET)
        discord_logger.propagate = True
        return

    discord_api_logging_handler: Handler = logging.FileHandler(
        filename=DISCORD_API_LOGGING_SETTINGS.file_name, encoding="utf-8", mode="a"
    )
    discord_api_logging_handler.setFormatter(
        logging.Formatter("{asctime}:{levelname}:{name}: {message}", style="{")
    )

    discord_logger.setLevel(DISCORD_API_LOGGING_SETTINGS.log_level)
    discord_logger.addHandler(discord_api_logging_handler)
    discord_logger.propagate = False


def apply_logging_settings(logging_settings: "LoggingSettings") -> None:
    """
    Apply the given logging settings to every logger TeX-Bot writes to.

    Safe to call repeatedly: existing handlers are replaced rather than added to,
    so reloading the configuration cannot accumulate duplicate handlers.
    """
    _apply_console_logging_settings(logging_settings)
    _apply_discord_channel_logging_settings(logging_settings)
    _apply_discord_api_logging_settings(logging_settings)
