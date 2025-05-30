"""Test suite for utils package."""

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
