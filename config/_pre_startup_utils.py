from collections.abc import Sequence

__all__: Sequence[str] = ("is_running_in_async",)


import asyncio


def is_running_in_async() -> bool:
    """Determine whether the current context is asynchronous or not."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    else:
        return True
