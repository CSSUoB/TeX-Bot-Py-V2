import sys
from types import TracebackType


class SuppressTraceback:
    def __init__(self) -> None:
        # noinspection SpellCheckingInspection
        self.previous_traceback_limit: int | None = getattr(sys, "tracebacklimit", None)

    def __enter__(self) -> None:
        # noinspection SpellCheckingInspection
        sys.tracebacklimit = 0

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType) -> None:  # noqa: E501
        if self.previous_traceback_limit is None:
            del sys.tracebacklimit
        else:
            # noinspection SpellCheckingInspection
            sys.tracebacklimit = self.previous_traceback_limit
