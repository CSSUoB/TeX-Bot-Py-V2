"""
Contains settings values and import & setup functions.

Settings values are imported from the .env file or the current environment variables.
These values are used to configure the functionality of the bot at run-time.
"""

import logging
from typing import TYPE_CHECKING

from ._settings import SettingsAccessor

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = ("settings",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

settings: "Final[SettingsAccessor]" = SettingsAccessor()
