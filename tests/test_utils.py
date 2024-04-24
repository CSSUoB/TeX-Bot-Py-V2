"""Test suite for utils package."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import random
import re
from typing import Final

import utils


class TestGenerateInviteURL:
    """Test case to unit-test the generate_invite_url utility function."""

    @staticmethod
    def test_url_generates() -> None:
        """Test that the invite URL generates successfully when valid arguments are passed."""
        DISCORD_BOT_APPLICATION_ID: Final[int] = random.randint(
            10000000000000000, 99999999999999999999,
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000, 99999999999999999999,
        )

        invite_url: str = utils.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID, DISCORD_GUILD_ID,
        )

        assert re.match(
            f"https://discord.com/.*={DISCORD_BOT_APPLICATION_ID}.*={DISCORD_GUILD_ID}",
            invite_url,
        )
