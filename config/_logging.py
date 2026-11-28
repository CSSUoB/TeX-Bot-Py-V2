"""
Application of the logging configuration held within the settings.

Logging is set up from the loaded settings rather than read directly from the
environment, so that changing a log level within the configuration file takes effect
upon the next reload without restarting TeX-Bot.
"""

import logging
from typing import TYPE_CHECKING, NamedTuple

from discord_logging.handler import DiscordHandler

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from logging import Handler, Logger
    from typing import Final

    from ._schema import (
        DiscordAPILoggingSettings,
        DiscordChannelLoggingSettings,
        LoggingSettings,
    )


__all__: Sequence[str] = (
    "DISCORD_LOGGER_NAME",
    "LOGGER_NAME",
    "apply_logging_settings",
    "relay_start_up_error_to_discord_log_channel",
    "set_discord_log_channel_identity",
)


# NOTE: These hold the *names* of the loggers to retrieve, rather than the loggers
# themselves, so `Final[str]` is the correct annotation despite what CAR201 infers
# from the variable names.
LOGGER_NAME: Final[str] = "TeX-Bot"  # noqa: CAR201

DISCORD_LOGGER_NAME: Final[str] = "discord"  # noqa: CAR201

DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME: Final[str] = "TeX-Bot"

logger: Final[Logger] = logging.getLogger(LOGGER_NAME)

discord_logger: Final[Logger] = logging.getLogger(DISCORD_LOGGER_NAME)


# NOTE: The name & avatar that logs are relayed into the Discord log channel under.
# TeX-Bot's own name & avatar are only known once it has logged in to Discord, so a
# placeholder is used until then. Held here, rather than only upon the handler, so
# that the handler created afresh by each reload is given them too.
class _DiscordLogChannelIdentity(NamedTuple):
    """The name & avatar that logs are relayed into the Discord log channel under."""

    display_name: str
    avatar_url: str | None


_discord_log_channel_identity: _DiscordLogChannelIdentity = _DiscordLogChannelIdentity(
    display_name=DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME, avatar_url=None
)


def _remove_handlers_of_type(
    target_logger: Logger, handler_type: type, *, excluding: type | None = None
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


def _apply_console_logging_settings(logging_settings: LoggingSettings) -> None:
    """Set up logging to the console output stream."""
    # NOTE: Handlers are replaced rather than reconfigured in place, so that applying
    # settings repeatedly (upon every reload) cannot accumulate duplicate handlers.
    _remove_handlers_of_type(logger, logging.StreamHandler, excluding=logging.FileHandler)

    console_logging_handler: Handler = logging.StreamHandler()
    console_logging_handler.setLevel(logging_settings.console.log_level)
    console_logging_handler.setFormatter(
        logging.Formatter("{asctime} | {name} | {levelname:^8} - {message}", style="{")
    )

    logger.addHandler(console_logging_handler)
    logger.propagate = False


def _apply_discord_channel_logging_settings(logging_settings: LoggingSettings) -> None:
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
        service_name=_discord_log_channel_identity.display_name,
        webhook_url=str(DISCORD_CHANNEL_LOGGING_SETTINGS.webhook_url),
        avatar_url=_discord_log_channel_identity.avatar_url,
    )
    discord_channel_logging_handler.setLevel(DISCORD_CHANNEL_LOGGING_SETTINGS.log_level)
    discord_channel_logging_handler.setFormatter(
        logging.Formatter("{levelname} | {message}", style="{")
    )

    logger.addHandler(discord_channel_logging_handler)


def _apply_lowest_destination_log_level(logging_settings: LoggingSettings) -> None:
    """
    Set TeX-Bot's logger to the lowest log level of any destination it writes to.

    The logger drops a record before any of its handlers see it, so each destination's
    own level is set upon its handler, & the logger must let through every record that
    at least one of those handlers will accept.
    """
    LOG_LEVEL_NUMBERS: Final[Mapping[str, int]] = logging.getLevelNamesMapping()

    lowest_log_level: int = LOG_LEVEL_NUMBERS[logging_settings.console.log_level]

    if logging_settings.discord_channel is not None:
        lowest_log_level = min(
            lowest_log_level, LOG_LEVEL_NUMBERS[logging_settings.discord_channel.log_level]
        )

    logger.setLevel(lowest_log_level)


def _apply_discord_api_logging_settings(logging_settings: LoggingSettings) -> None:
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


def set_discord_log_channel_identity(display_name: str, avatar_url: str | None) -> None:
    """
    Relay every log sent into the Discord log channel under the given name & avatar.

    Called once TeX-Bot has logged in to Discord, which is when its own name & avatar
    first become known. Applies to the handler already relaying logs, & to the one
    created afresh by any later reload.
    """
    global _discord_log_channel_identity  # noqa: PLW0603

    _discord_log_channel_identity = _DiscordLogChannelIdentity(
        display_name=display_name, avatar_url=avatar_url
    )

    existing_handler: Handler
    for existing_handler in logger.handlers:
        if not isinstance(existing_handler, DiscordHandler):
            continue

        existing_handler.service_name = display_name
        existing_handler.avatar_url = avatar_url


def relay_start_up_error_to_discord_log_channel(
    start_up_error: Exception, webhook_url: str
) -> None:
    """
    Send an error that stopped TeX-Bot from starting up to the Discord log channel.

    Sent through a handler of its own, rather than through TeX-Bot's logger: logging
    has not been set up at all when the configuration itself is invalid, & doing so
    also keeps the error from being printed to the console a second time.
    """
    start_up_error_handler: Handler = DiscordHandler(
        service_name=_discord_log_channel_identity.display_name,
        webhook_url=webhook_url,
        avatar_url=_discord_log_channel_identity.avatar_url,
        # NOTE: Sent once, without waiting to retry, so that an unreachable webhook
        # cannot hold up the error being raised for long.
        rate_limit_retry=False,
        discord_timeout=3,
    )
    start_up_error_handler.setFormatter(
        logging.Formatter("{levelname} | {message}", style="{")
    )

    try:
        start_up_error_handler.handle(
            logging.makeLogRecord(
                {
                    "name": LOGGER_NAME,
                    "levelno": logging.ERROR,
                    "levelname": "ERROR",
                    "msg": str(start_up_error),
                }
            )
        )
    finally:
        start_up_error_handler.close()


def apply_logging_settings(logging_settings: LoggingSettings) -> None:
    """
    Apply the given logging settings to every logger TeX-Bot writes to.

    Safe to call repeatedly: existing handlers are replaced rather than added to,
    so reloading the configuration cannot accumulate duplicate handlers.
    """
    _apply_console_logging_settings(logging_settings)
    _apply_lowest_destination_log_level(logging_settings)
    _apply_discord_channel_logging_settings(logging_settings)
    _apply_discord_api_logging_settings(logging_settings)
