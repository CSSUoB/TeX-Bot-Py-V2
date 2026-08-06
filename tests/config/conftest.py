"""Shared fixtures & constants for the config package test suite."""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
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
