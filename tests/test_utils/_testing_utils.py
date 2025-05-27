from collections.abc import Sequence

__all__: Sequence[str] = ("EmptyContextManager",)

from types import TracebackType


class EmptyContextManager:
    """Empty context manager that executes no logic when entering/exiting."""

    def __enter__(self) -> None:
        """Enter the context manager and execute no additional logic."""

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:  # noqa: E501
        """Exit the context manager and execute no additional logic."""
