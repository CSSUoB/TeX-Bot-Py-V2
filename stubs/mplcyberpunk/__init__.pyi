from collections.abc import Sequence

import matplotlib

__all__: Sequence[str] = ("add_bar_gradient",)

def add_bar_gradient(
    bars: matplotlib.container.BarContainer,
    ax: matplotlib.axes.Axes | None = ...,
    horizontal: bool = ...,
) -> None: ...
