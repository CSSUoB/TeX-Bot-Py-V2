"""Shared fixtures & constants for the config package test suite."""

import logging
from typing import TYPE_CHECKING

import pytest

from config._logging import DISCORD_LOGGER_NAME, LOGGER_NAME

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from logging import Handler, Logger
    from pathlib import Path
    from typing import Final

    type ConfigWriter = "Callable[[str], Path]"


__all__: "Sequence[str]" = (
    "CHANGED_EASTER_EGG_PROBABILITY",
    "DEFAULT_EASTER_EGG_PROBABILITY",
    "MINIMAL_CONFIG",
    "VALID_BOT_TOKEN",
    "VALID_MAIN_GUILD_ID",
    "VALID_WEBHOOK_URL",
)


# NOTE: A fabricated value, structured to satisfy the bot-token pattern:
# 24-26 characters, then 6, then 27-38.
VALID_BOT_TOKEN: "Final[str]" = "MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs"  # noqa: S105

VALID_MAIN_GUILD_ID: "Final[int]" = 1234567890123456789

VALID_WEBHOOK_URL: "Final[str]" = "https://discord.com/api/webhooks/123456789/abcdefg"

DEFAULT_EASTER_EGG_PROBABILITY: "Final[float]" = 0.01

CHANGED_EASTER_EGG_PROBABILITY: "Final[float]" = 0.5

MINIMAL_CONFIG: "Final[str]" = f"""\
# A deployment configuration holding only the settings that are required.
discord:
  bot-token: {VALID_BOT_TOKEN}
  main-guild-id: {VALID_MAIN_GUILD_ID}
community-group:
  links: {{}}
  msl: {{}}
"""


@pytest.fixture(autouse=True)
def _restore_loggers() -> "Iterator[None]":
    """
    Restore both loggers to the state they were in before each test.

    Logging is process-wide, so without this any test that applied a configuration
    (including every test that reloads one, or runs `/config reload`) would leave its
    handlers, level & propagation attached for every test that ran afterwards, making
    the results depend upon the order the tests happened to be collected in.
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


@pytest.fixture()
def write_config(tmp_path: "Path") -> "ConfigWriter":
    """Return a callable writing the given YAML into a configuration file."""

    def _write_config(raw_yaml: str) -> "Path":
        config_file_path: Path = tmp_path / "tex-bot-deployment.yaml"
        config_file_path.write_text(raw_yaml, encoding="utf-8")
        return config_file_path

    return _write_config


@pytest.fixture()
def config_file(write_config: "ConfigWriter") -> "Path":
    """Return the path of a configuration file holding only the required settings."""
    return write_config(MINIMAL_CONFIG)
