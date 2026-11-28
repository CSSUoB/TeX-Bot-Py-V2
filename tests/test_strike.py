"""Test suite for the strike commands."""

__all__: Sequence[str] = ("TestReportedMessageDestination",)

import asyncio
lazy from collections.abc import Sequence
lazy from pathlib import Path
lazy from types import SimpleNamespace
lazy from typing import Final, cast

import pytest
lazy import discord

import config
from config._accessor import SettingsAccessor
lazy from cogs.strike import StrikeContextCommandsCog
lazy from utils import TeXBot, TeXBotApplicationContext

# NOTE: A fabricated value, structured to satisfy the bot-token pattern:
# 24-26 characters, then 6, then 27-38.
VALID_BOT_TOKEN: Final[str] = "MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs"  # noqa: S105

REQUIRED_SETTINGS_YAML: Final[str] = (
    f"discord:\n  bot-token: {VALID_BOT_TOKEN}\n  main-guild-id: 1234567890123456789\n"
)


@pytest.fixture(scope="module", autouse=True)
def _load_required_settings(tmp_path_factory: pytest.TempPathFactory) -> None:
    """
    Load a valid configuration before any cog is imported.

    Importing any cog loads every other one alongside it, several of which read the
    configuration as they are imported, so a valid configuration must already be loaded
    before the import can succeed at all.
    """
    CONFIG_FILE_PATH: Final[Path] = tmp_path_factory.mktemp("strike") / "tex-bot.yaml"
    CONFIG_FILE_PATH.write_text(REQUIRED_SETTINGS_YAML, encoding="utf-8")

    config.settings.reload(CONFIG_FILE_PATH)


class TestReportedMessageDestination:
    """Test case for the channel that reported messages are sent to."""

    @staticmethod
    def test_the_configured_channel_is_used(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that a reported message is sent to the channel named within the settings.

        A "#discord" channel exists but is not the one configured, so finding it instead
        would mean the setting had been ignored.
        """
        CONFIG_FILE_PATH: Final[Path] = tmp_path / "tex-bot.yaml"
        CONFIG_FILE_PATH.write_text(
            f"{REQUIRED_SETTINGS_YAML}"
            "commands:\n"
            "  strike:\n"
            "    reported-message-destination-channel: mod-reports\n",
            encoding="utf-8",
        )
        settings_accessor: SettingsAccessor = SettingsAccessor()
        settings_accessor.reload(CONFIG_FILE_PATH)
        monkeypatch.setattr("cogs.strike.settings", settings_accessor)

        # NOTE: The cog is created without its constructor, & given a stand-in for the
        # running bot, so that no connection to Discord is needed.
        cog: StrikeContextCommandsCog = StrikeContextCommandsCog.__new__(
            StrikeContextCommandsCog
        )
        cog.bot = cast(
            "TeXBot",
            SimpleNamespace(
                main_guild=SimpleNamespace(text_channels=[SimpleNamespace(name="discord")])
            ),
        )

        error_messages: list[str] = []

        async def _command_send_error(_ctx: object, message: str) -> None:
            error_messages.append(message)

        monkeypatch.setattr(cog, "command_send_error", _command_send_error)

        asyncio.run(
            cog._send_message_to_committee(  # noqa: SLF001
                cast("TeXBotApplicationContext", None), cast("discord.Message", None)
            )
        )

        assert error_messages == [
            "Could not find the `#mod-reports` channel in the main guild!"
        ]
