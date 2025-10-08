"""Contains cog classes for any stats calculations and handling."""

import io
import math
from typing import TYPE_CHECKING

import discord
import matplotlib.pyplot
import mplcyberpunk

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping, Sequence

    from matplotlib.text import Text as Plot_Text

__all__: Sequence[str] = ("amount_of_time_formatter", "plot_bar_chart")


def amount_of_time_formatter(value: float, time_scale: str) -> str:
    """
    Format the amount of time value according to the provided time_scale.

    E.g. past "1 days" => past "day",
    past "2.00 weeks" => past "2 weeks",
    past "3.14159 months" => past "3.14 months"
    """
    if value == 1 or float(f"{value:.2f}") == 1:
        return f"{time_scale}"

    if value % 1 == 0 or float(f"{value:.2f}") % 1 == 0:
        return f"{int(value)} {time_scale}s"

    return f"{value:.2f} {time_scale}s"


def plot_bar_chart(
    data: Mapping[str, int],
    x_label: str,
    y_label: str,
    title: str,
    filename: str,
    description: str,
    extra_text: str = "",
) -> discord.File:
    """Generate an image of a plot bar chart from the given data and format variables."""
    matplotlib.pyplot.style.use("cyberpunk")

    max_data_value: int = max(data.values()) + 1

    data = dict(data)

    # NOTE: The "extra_values" dictionary represents columns of data that should be formatted differently to the standard data columns
    extra_values: dict[str, int] = {}
    if "Total" in data:
        extra_values["Total"] = data.pop("Total")

    if len(data) > 4:
        data = {
            key: value
            for index, (key, value) in enumerate(data.items())
            if value > 0 or index <= 4
        }

    bars = matplotlib.pyplot.bar(*zip(*data.items(), strict=True))

    if extra_values:
        extra_bars = matplotlib.pyplot.bar(*zip(*extra_values.items(), strict=True))
        mplcyberpunk.add_bar_gradient(extra_bars)

    mplcyberpunk.add_bar_gradient(bars)

    x_tick_labels: Collection[Plot_Text] = matplotlib.pyplot.gca().get_xticklabels()
    count_x_tick_labels: int = len(x_tick_labels)

    index: int
    tick_label: Plot_Text
    for index, tick_label in enumerate(x_tick_labels):
        if tick_label.get_text() == "Total":
            tick_label.set_fontweight("bold")

        # NOTE: Shifts the y location of every other horizontal label down so that they do not overlap with one-another
        if index % 2 == 1 and count_x_tick_labels > 4:
            tick_label.set_y(tick_label.get_position()[1] - 0.044)

    matplotlib.pyplot.yticks(range(0, max_data_value, math.ceil(max_data_value / 15)))

    x_label_obj: Plot_Text = matplotlib.pyplot.xlabel(
        x_label, fontweight="bold", fontsize="large", wrap=True
    )
    x_label_obj._get_wrap_line_width = lambda: 475  # type: ignore[attr-defined]

    y_label_obj: Plot_Text = matplotlib.pyplot.ylabel(
        y_label, fontweight="bold", fontsize="large", wrap=True
    )
    y_label_obj._get_wrap_line_width = lambda: 375  # type: ignore[attr-defined]

    title_obj: Plot_Text = matplotlib.pyplot.title(title, fontsize="x-large", wrap=True)
    title_obj._get_wrap_line_width = lambda: 500  # type: ignore[attr-defined]

    if extra_text:
        extra_text_obj: Plot_Text = matplotlib.pyplot.text(
            0.5,
            -0.27,
            extra_text,
            ha="center",
            transform=matplotlib.pyplot.gca().transAxes,
            wrap=True,
            fontstyle="italic",
            fontsize="small",
        )
        extra_text_obj._get_wrap_line_width = lambda: 400  # type: ignore[attr-defined]
        matplotlib.pyplot.subplots_adjust(bottom=0.2)

    plot_file = io.BytesIO()
    matplotlib.pyplot.savefig(plot_file, format="png")
    matplotlib.pyplot.close()
    plot_file.seek(0)

    discord_plot_file: discord.File = discord.File(
        plot_file, filename, description=description
    )

    plot_file.close()

    return discord_plot_file
