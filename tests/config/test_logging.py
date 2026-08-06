"""Test suite for applying the logging configuration."""

import logging
from typing import TYPE_CHECKING

import pytest
from discord_logging.handler import DiscordHandler

from config._logging import (
    DISCORD_LOGGER_NAME,
    LOGGER_NAME,
    apply_logging_settings,
)
from config._schema import SettingsSchema

from .conftest import VALID_BOT_TOKEN, VALID_MAIN_GUILD_ID, VALID_WEBHOOK_URL

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence
    from logging import Handler, Logger
    from pathlib import Path
    from typing import Final

    from config._schema import LoggingSettings

__all__: "Sequence[str]" = ()


REQUIRED_SETTINGS: "Final[Mapping[str, object]]" = {
    "discord": {"bot-token": VALID_BOT_TOKEN, "main-guild-id": VALID_MAIN_GUILD_ID},
    "community-group": {"links": {}, "msl": {}},
}


def _logging_settings(**logging_overrides: object) -> "LoggingSettings":
    """Build the logging section of a validated configuration."""
    return SettingsSchema.model_validate(
        {**REQUIRED_SETTINGS, "logging": logging_overrides}
    ).logging


@pytest.fixture(autouse=True)
def _restore_loggers() -> "Iterator[None]":
    """
    Restore both loggers to the state they were in before each test.

    Logging is process-wide, so without this a test applying a configuration would
    leave its handlers attached for every test that ran afterwards.
    """
    tex_bot_logger: Logger = logging.getLogger(LOGGER_NAME)
    discord_logger: Logger = logging.getLogger(DISCORD_LOGGER_NAME)

    ORIGINAL_STATE: Final[Sequence[tuple[Logger, Sequence[Handler], int, bool]]] = tuple(
        (
            single_logger,
            tuple(single_logger.handlers),
            single_logger.level,
            single_logger.propagate,
        )
        for single_logger in (tex_bot_logger, discord_logger)
    )

    yield

    single_logger: Logger
    original_handlers: Sequence[Handler]
    original_level: int
    original_propagate: bool
    for single_logger, original_handlers, original_level, original_propagate in ORIGINAL_STATE:
        single_logger.handlers = list(original_handlers)
        single_logger.setLevel(original_level)
        single_logger.propagate = original_propagate


def _handlers_of_type(logger_name: str, handler_type: type) -> "Sequence[Handler]":
    """Return every handler of the given type attached to the named logger."""
    return tuple(
        handler
        for handler in logging.getLogger(logger_name).handlers
        if isinstance(handler, handler_type)
    )


class TestConsoleLogging:
    """Test case for logging to the console output stream."""

    @staticmethod
    def test_console_log_level_is_applied() -> None:
        """Test that the configured log level is set upon the logger."""
        apply_logging_settings(_logging_settings(console={"log-level": "WARNING"}))

        assert logging.getLogger(LOGGER_NAME).level == logging.WARNING

    @staticmethod
    def test_a_console_handler_is_attached() -> None:
        """Test that logs are emitted to the console output stream."""
        apply_logging_settings(_logging_settings())

        assert len(_handlers_of_type(LOGGER_NAME, logging.StreamHandler)) == 1

    @staticmethod
    def test_applying_settings_repeatedly_does_not_accumulate_handlers() -> None:
        """
        Test that applying the logging configuration many times attaches one handler.

        Handlers are replaced rather than added to, because an accumulated handler
        would cause every log record to be emitted more than once.
        """
        for log_level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            apply_logging_settings(_logging_settings(console={"log-level": log_level}))

        assert len(_handlers_of_type(LOGGER_NAME, logging.StreamHandler)) == 1


class TestDiscordChannelLogging:
    """Test case for relaying error logs to a Discord log channel."""

    @staticmethod
    def test_no_handler_is_attached_when_the_section_is_omitted() -> None:
        """Test that omitting the Discord log-channel section attaches no handler."""
        apply_logging_settings(_logging_settings())

        assert not _handlers_of_type(LOGGER_NAME, DiscordHandler)

    @staticmethod
    def test_a_handler_is_attached_when_a_webhook_is_configured() -> None:
        """Test that configuring a webhook URL relays logs to that Discord channel."""
        apply_logging_settings(
            _logging_settings(
                **{"discord-channel": {"webhook-url": VALID_WEBHOOK_URL, "log-level": "ERROR"}}
            )
        )

        DISCORD_HANDLERS: Final[Sequence[Handler]] = _handlers_of_type(
            LOGGER_NAME, DiscordHandler
        )

        assert len(DISCORD_HANDLERS) == 1
        assert DISCORD_HANDLERS[0].level == logging.ERROR

    @staticmethod
    def test_removing_the_webhook_detaches_the_handler() -> None:
        """Test that removing the Discord log-channel section stops relaying logs."""
        apply_logging_settings(
            _logging_settings(**{"discord-channel": {"webhook-url": VALID_WEBHOOK_URL}})
        )
        assert _handlers_of_type(LOGGER_NAME, DiscordHandler)

        apply_logging_settings(_logging_settings())

        assert not _handlers_of_type(LOGGER_NAME, DiscordHandler)


class TestDiscordAPILogging:
    """Test case for recording the logs emitted by the Discord API wrapper."""

    @staticmethod
    def test_no_handler_is_attached_when_disabled() -> None:
        """Test that Discord API logs are not recorded unless they are enabled."""
        apply_logging_settings(_logging_settings(**{"discord-api": {"enabled": False}}))

        assert not _handlers_of_type(DISCORD_LOGGER_NAME, logging.FileHandler)

    @staticmethod
    def test_a_file_handler_is_attached_when_enabled(tmp_path: "Path") -> None:
        """Test that enabling Discord API logging writes them to the configured file."""
        LOG_FILE_PATH: Final[Path] = tmp_path / "discord.log"

        apply_logging_settings(
            _logging_settings(
                **{
                    "discord-api": {
                        "enabled": True,
                        "log-level": "DEBUG",
                        "file-name": str(LOG_FILE_PATH),
                    }
                }
            )
        )

        FILE_HANDLERS: Final[Sequence[Handler]] = _handlers_of_type(
            DISCORD_LOGGER_NAME, logging.FileHandler
        )

        assert len(FILE_HANDLERS) == 1
        assert logging.getLogger(DISCORD_LOGGER_NAME).level == logging.DEBUG

    @staticmethod
    def test_disabling_afterwards_detaches_the_handler(tmp_path: "Path") -> None:
        """Test that disabling Discord API logging stops recording it."""
        apply_logging_settings(
            _logging_settings(
                **{
                    "discord-api": {
                        "enabled": True,
                        "file-name": str(tmp_path / "discord.log"),
                    }
                }
            )
        )
        assert _handlers_of_type(DISCORD_LOGGER_NAME, logging.FileHandler)

        apply_logging_settings(_logging_settings(**{"discord-api": {"enabled": False}}))

        assert not _handlers_of_type(DISCORD_LOGGER_NAME, logging.FileHandler)
