"""Decorator to wrap a class method as a read-only class property."""

from collections.abc import Callable
from typing import Any


class classproperty:  # noqa: N801
    """Decorator to wrap a class method as a read-only class property."""

    def __init__(self, func: Callable[[Any], Any]) -> None:
        """Initialise the decorator around the given function."""
        # noinspection SpellCheckingInspection
        self.fget: Callable[[Any], Any] = func

    def __get__(self, instance: Any | None, owner: type) -> Any:
        """Retrieve the read-only property from the class/instance."""
        return self.fget(owner)
