"""Functions to enable interaction with MSL based SU websites."""

from collections.abc import Sequence

__all__: Sequence[str] = ("",)


import logging
from logging import Logger
from typing import Final

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class MSL:
    """Class to define the functions related to MSL based SU websites."""

    async def _get_msl_context(self, url: str) -> tuple[dict[str, str], dict[str, str]]:
        """Get the required context headers, data and cookies to make a request to MSL."""
        return {}, {}

