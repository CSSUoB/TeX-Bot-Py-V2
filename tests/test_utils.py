"""Test suite for utils package."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import random
import re
from typing import Final

import utils

# TODO(CarrotManMatt): Move to stats_tests  # noqa: FIX002
# https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/57
# class TestPlotBarChart:
#     """Test case to unit-test the plot_bar_chart function."""
#
#     def test_bar_chart_generates(self) -> None:
#         """Test that the bar chart generates successfully when valid arguments are passed."""  # noqa: ERA001, E501, W505
#         FILENAME: Final[str] = "output_chart.png"  # noqa: ERA001
#         DESCRIPTION: Final[str] = "Bar chart of the counted value of different roles."  # noqa: ERA001, E501, W505
#
#         bar_chart_image: discord.File = plot_bar_chart(
#             data={"role1": 5, "role2": 7},  # noqa: ERA001
#             x_label="Role Name",  # noqa: ERA001
#             y_label="Counted value",  # noqa: ERA001
#             title="Counted Value Of Each Role",  # noqa: ERA001
#             filename=FILENAME,  # noqa: ERA001
#             description=DESCRIPTION,  # noqa: ERA001
#             extra_text="This is extra text"  # noqa: ERA001
#         )  # noqa: ERA001, RUF100
#
#         assert bar_chart_image.filename == FILENAME  # noqa: ERA001
#         assert bar_chart_image.description == DESCRIPTION  # noqa: ERA001
#         assert bool(bar_chart_image.fp.read()) is True  # noqa: ERA001


# TODO(CarrotManMatt): Move to stats_tests  # noqa: FIX002
# https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/57
# class TestAmountOfTimeFormatter:
#     """Test case to unit-test the amount_of_time_formatter function."""
#
#     @pytest.mark.parametrize(
#         "time_value",
#         (1, 1.0, 0.999999, 1.000001)  # noqa: ERA001
#     )  # noqa: ERA001, RUF100
#     def test_format_unit_value(self, time_value: float) -> None:
#         """Test that a value of one only includes the time_scale."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         formatted_amount_of_time: str = amount_of_time_formatter(time_value, TIME_SCALE)  # noqa: ERA001, E501, W505
#
#         assert formatted_amount_of_time == TIME_SCALE  # noqa: ERA001
#         assert not formatted_amount_of_time.endswith("s")  # noqa: ERA001
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
