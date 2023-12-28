"""
Context manager to suppress the traceback output when an exception is raised.

The previous traceback limit is returned when exiting the context manager.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ("SuppressTraceback",)

import sys
from types import TracebackType


class SuppressTraceback:
    """
    Context manager to suppress the traceback output when an exception is raised.

    The previous traceback limit is returned when exiting the context manager.
    """

    def __init__(self) -> None:
        # noinspection SpellCheckingInspection
        """
        Initialise a new SuppressTraceback context manager instance.

        The current value of `sys.tracebacklimit` is stored for future reference
        to revert back to upon exiting the context manager.
        """
        # noinspection SpellCheckingInspection
        self.previous_traceback_limit: int | None = getattr(sys, "tracebacklimit", None)

    def __enter__(self) -> None:
        """Enter the context manager, suppressing the traceback output."""
        # noinspection SpellCheckingInspection
        sys.tracebacklimit = 0

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType) -> None:  # noqa: E501
        """Exit the context manager, reverting the limit of traceback output."""
        if self.previous_traceback_limit is None:
            del sys.tracebacklimit
        else:
            # noinspection SpellCheckingInspection
            sys.tracebacklimit = self.previous_traceback_limit
