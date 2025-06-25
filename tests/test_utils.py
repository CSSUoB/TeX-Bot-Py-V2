"""Test suite for utils package."""

import asyncio
import random
import re
from typing import TYPE_CHECKING

import utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

__all__: "Sequence[str]" = ()


class TestGenerateInviteURL:
    """Test case to unit-test the generate_invite_url utility function."""

    @staticmethod
    def test_url_generates() -> None:
        """Test that the invite URL generates successfully when valid arguments are passed."""
        DISCORD_BOT_APPLICATION_ID: Final[int] = random.randint(  # noqa: S311
            10000000000000000,
            99999999999999999999,
        )
        DISCORD_MAIN_GUILD_ID: Final[int] = random.randint(  # noqa: S311
            10000000000000000,
            99999999999999999999,
        )

        invite_url: str = utils.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_MAIN_GUILD_ID,
        )

        assert re.fullmatch(
            (
                r"\Ahttps://discord.com/.*="
                + str(DISCORD_BOT_APPLICATION_ID)
                + r".*="
                + str(DISCORD_MAIN_GUILD_ID)
                + r".*\Z"
            ),
            invite_url,
        )


class TestIsRunningInAsync:
    """Test case to unit-test the is_running_in_async utility function."""

    @staticmethod
    def test_is_running_in_async() -> None:
        """Test that the is_running_in_async function returns True when called in an async context."""  # noqa: E501, W505

        async def async_test() -> None:
            """Async function to test the is_running_in_async utility."""
            assert utils.is_running_in_async() is True

        asyncio.run(async_test())

    @staticmethod
    def test_is_not_running_in_async() -> None:
        """Test that the is_running_in_async function returns False when called in a non-async context."""  # noqa: E501, W505
        assert utils.is_running_in_async() is False
