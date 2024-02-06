"""Automated test suite for the `stats.py` cog."""
import random
import string
from typing import Final

import discord
import pytest
from classproperties import classproperty
from discord import MessageCommand, SlashCommand, UserCommand

from cogs.stats import (
    StatsCommandsCog,
    amount_of_time_formatter,
    plot_bar_chart,
)

# noinspection PyProtectedMember
from tests._testing_utils import BaseTestDiscordCommand

# noinspection PyProtectedMember
from tests._testing_utils.pycord_internals import TestingApplicationContext


class TestAmountOfTimeFormatter:
    """Test case to unit-test the amount_of_time_formatter function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_TIME_VALUE", (1, 1.0, 0.999999, 1.000001))
    @pytest.mark.parametrize("TIME_SCALE", ("day",))
    def test_format_unit_value(self, TEST_TIME_VALUE: float, TIME_SCALE: str) -> None:  # noqa: N803
        """Test that a value of one only includes the time_scale."""
        formatted_amount_of_time: str = amount_of_time_formatter(TEST_TIME_VALUE, TIME_SCALE)

        assert formatted_amount_of_time == TIME_SCALE
        assert not formatted_amount_of_time.endswith("s")

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_TIME_VALUE",
        (*range(2, 21), 2.00, 0, 0.0, 25.0, -0, -0.0, -25.0)
    )
    @pytest.mark.parametrize("TIME_SCALE", ("day",))
    def test_format_integer_value(self, TEST_TIME_VALUE: float, TIME_SCALE: str) -> None:  # noqa: N803
        """Test that an integer value includes the value and time_scale pluralized."""
        assert amount_of_time_formatter(
            TEST_TIME_VALUE,
            TIME_SCALE
        ) == f"{int(TEST_TIME_VALUE)} {TIME_SCALE}s"

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_TIME_VALUE", (3.14159, 0.005, 25.0333333))
    @pytest.mark.parametrize("TIME_SCALE", ("day",))
    def test_format_float_value(self, TEST_TIME_VALUE: float, TIME_SCALE: str) -> None:  # noqa: N803
        """Test that a float value includes the rounded value and time_scale pluralized."""
        assert amount_of_time_formatter(
            TEST_TIME_VALUE,
            TIME_SCALE
        ) == f"{TEST_TIME_VALUE:.2f} {TIME_SCALE}s"


class TestPlotBarChart:
    """Test case to unit-test the plot_bar_chart function."""

    def test_bar_chart_generates(self) -> None:
        """Test that the bar chart generates successfully when valid arguments are passed."""
        FILENAME: Final[str] = "output_chart.png"
        DESCRIPTION: Final[str] = "Bar chart of the counted value of different roles."

        bar_chart_image: discord.File = plot_bar_chart(
            data={"role1": 5, "role2": 7},
            x_label="Role Name",
            y_label="Counted value",
            title="Counted Value Of Each Role",
            filename=FILENAME,
            description=DESCRIPTION,
            extra_text="This is extra text"
        )

        assert bar_chart_image.filename == FILENAME
        assert bar_chart_image.description == DESCRIPTION
        assert bool(bar_chart_image.fp.read()) is True


class TestStatsCommandGroup:
    """Test case to unit-test the stats command group within the `StatsCommandsCog`."""

    def test_command_group_description(self) -> None:
        """Test that the stats command group has a valid description."""
        assert "stat" in StatsCommandsCog.stats.description.lower()
        assert "Discord server" in StatsCommandsCog.stats.description
        assert (
            "the " in StatsCommandsCog.stats.description
            or "our community group's" in StatsCommandsCog.stats.description
        )


class TestChannelStatsCommand(BaseTestDiscordCommand):
    """Test case to unit-test the channel stats command."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def COMMAND(cls) -> SlashCommand | UserCommand | MessageCommand:  # noqa: N802,N805
        """The Discord command the cog, linked to this test case, has the functionality for."""  # noqa: D401
        # noinspection PyTypeChecker
        return StatsCommandsCog.channel_stats

    def test_command_description(self) -> None:
        """Test that the channel stats command has a valid description."""
        assert "stats" in StatsCommandsCog.channel_stats.description.lower()
        assert "channel" in StatsCommandsCog.channel_stats.description.lower()

    def test_command_option(self) -> None:
        """Test that the channel stats command has an option with the correct details."""
        discord.Bot().load_extension("cogs")  # type: ignore[no-untyped-call]

        assert any(
            (
                "channel" in option.description
                and "stats" in option.description
                and option._parameter_name is not None  # noqa: SLF001
                and "id" in option._parameter_name.lower()  # noqa: SLF001
            )
            for option
            in StatsCommandsCog.channel_stats.options
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_CHANNEL_ID",
        (
            "INVALID_CHANNEL_ID",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=18)
            ),
            "".join(random.choices(string.digits, k=2)),
            "".join(random.choices(string.digits, k=50))
        )
    )
    def test_invalid_channel_id(self, INVALID_CHANNEL_ID: str, CONTEXT: TestingApplicationContext) -> None:  # noqa: N803, E501
        """Test that an error occurs when running the command with an invalid channel ID."""
        self.execute_command(
            ctx=CONTEXT,
            str_channel_id=INVALID_CHANNEL_ID
        )

        assert len(CONTEXT.interaction.responses) == 1
        assert CONTEXT.interaction.responses[0].content is not None
        assert (
            f"{INVALID_CHANNEL_ID!r} is not a valid channel ID"
            in CONTEXT.interaction.responses[0].content
        )
