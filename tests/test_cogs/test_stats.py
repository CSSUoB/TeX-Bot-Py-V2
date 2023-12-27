"""Automated test suite for the `stats.py` cog."""

from typing import Final

import discord
import pytest

# from cogs.stats import amount_of_time_formatter, plot_bar_chart


# class TestAmountOfTimeFormatter:
#     """Test case to unit-test the amount_of_time_formatter function."""
#
#     @pytest.mark.parametrize(
#         "time_value",
#         (1, 1.0, 0.999999, 1.000001)
#     )
#     def test_format_unit_value(self, time_value: float) -> None:
#         """Test that a value of one only includes the time_scale."""
#         TIME_SCALE: Final[str] = "day"
#
#         formatted_amount_of_time: str = amount_of_time_formatter(time_value, TIME_SCALE)
#
#         assert formatted_amount_of_time == TIME_SCALE
#         assert not formatted_amount_of_time.endswith("s")
#
#     @pytest.mark.parametrize(
#         "time_value",
#         (*range(2, 21), 2.00, 0, 0.0, 25.0, -0, -0.0, -25.0)  # noqa: ERA001
#     )  # noqa: ERA001, RUF100
#     def test_format_integer_value(self, time_value: float) -> None:
#         """Test that an integer value includes the value and time_scale pluralized."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         assert amount_of_time_formatter(
#             time_value,
#             TIME_SCALE
#         ) == f"{int(time_value)} {TIME_SCALE}s"
#
#     @pytest.mark.parametrize("time_value", (3.14159, 0.005, 25.0333333))
#     def test_format_float_value(self, time_value: float) -> None:
#         """Test that a float value includes the rounded value and time_scale pluralized."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         assert amount_of_time_formatter(
#             time_value,
#             TIME_SCALE
#         ) == f"{time_value:.2f} {TIME_SCALE}s"
#
#
# class TestPlotBarChart:
#     """Test case to unit-test the plot_bar_chart function."""
#
#     def test_bar_chart_generates(self) -> None:
#         """Test that the bar chart generates successfully when valid arguments are passed."""
#         FILENAME: Final[str] = "output_chart.png"
#         DESCRIPTION: Final[str] = "Bar chart of the counted value of different roles."
#
#         bar_chart_image: discord.File = plot_bar_chart(
#             data={"role1": 5, "role2": 7},
#             x_label="Role Name",
#             y_label="Counted value",
#             title="Counted Value Of Each Role",
#             filename=FILENAME,
#             description=DESCRIPTION,
#             extra_text="This is extra text"
#         )
#
#         assert bar_chart_image.filename == FILENAME
#         assert bar_chart_image.description == DESCRIPTION
#         assert bool(bar_chart_image.fp.read()) is True
