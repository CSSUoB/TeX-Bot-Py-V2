"""Automated test suite for the `stats.py` cog."""
from typing import TYPE_CHECKING, Final

import pytest

from cogs.stats import StatsCommandsCog, amount_of_time_formatter, plot_bar_chart  # BUG: Importing any cogs loads all other cogs which then sets up the Env variables & fails

if TYPE_CHECKING:
    import discord


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


class TestChannelStatsCommand:
    """Test case to unit-test the channel stats command."""

    def test_command_description(self) -> None:
        """Test that the channel stats command has a valid description."""
        assert "stats" in StatsCommandsCog.channel_stats.description.lower()
        assert "channel" in StatsCommandsCog.channel_stats.description.lower()
