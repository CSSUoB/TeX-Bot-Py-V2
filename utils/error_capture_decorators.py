"""
Common decorator utilities to capture & suppress errors.

Capturing errors is necessary in contexts where exceptions are not already suppressed.
"""

from collections.abc import Sequence

__all__: Sequence[str] = [
    "ErrorCaptureDecorators",
    "capture_guild_does_not_exist_error",
    "capture_strike_tracking_error"
]

import functools
import logging
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, Final, ParamSpec, TypeVar

from exceptions import GuildDoesNotExist, StrikeTrackingError
from utils.tex_bot_base_cog import TeXBotBaseCog

P = ParamSpec("P")
T = TypeVar("T")

if TYPE_CHECKING:
    from typing import Concatenate, TypeAlias

    WrapperInputFunc: TypeAlias = Callable[  # type: ignore[valid-type, misc]
        Concatenate[TeXBotBaseCog, P] | P,
        Coroutine[Any, Any, T]
    ]
    WrapperOutputFunc: TypeAlias = Callable[  # type: ignore[valid-type, misc]
        Concatenate[TeXBotBaseCog, P] | P,
        Coroutine[Any, Any, T | None]
    ]
    DecoratorInputFunc: TypeAlias = Callable[
        Concatenate[TeXBotBaseCog, P],
        Coroutine[Any, Any, T]
    ]


class ErrorCaptureDecorators:
    """
    Common decorator utilities to capture & suppress errors.

    Capturing errors is necessary in contexts where exceptions are not already suppressed.
    """

    @staticmethod
    def capture_error_and_close(func: "DecoratorInputFunc[P, T]", error_type: type[BaseException], close_func: Callable[[BaseException], None]) -> "WrapperOutputFunc[P, T]":  # noqa: E501
        """
        Decorator to send an error message to the user when the given exception type is raised.

        The raised exception is then suppressed.
        """  # noqa: D401
        @functools.wraps(func)
        async def wrapper(self: TeXBotBaseCog, /, *args: P.args, **kwargs: P.kwargs) -> T | None:  # noqa: E501
            if not isinstance(self, TeXBotBaseCog):
                INVALID_METHOD_TYPE_MESSAGE: Final[str] = (  # type: ignore[unreachable]
                    f"Parameter {self.__name__!r} of any 'capture_error' decorator "
                    f"must be an instance of {TeXBotBaseCog.__name__!r}/one of its subclasses."
                )
                raise TypeError(INVALID_METHOD_TYPE_MESSAGE)
            try:
                return await func(self, *args, **kwargs)
            except error_type as error:
                close_func(error)
                await self.bot.close()
                return None
        return wrapper

    @staticmethod
    def critical_error_close_func(error: BaseException) -> None:
        """Component function to send logging messages when a critical error is encountered."""
        logging.critical(str(error).rstrip(".:"))

    @classmethod
    def strike_tracking_error_close_func(cls, error: BaseException) -> None:
        """Component function to send logging messages when a StrikeTrackingError is raised."""
        cls.critical_error_close_func(error)
        logging.warning("Critical errors are likely to lead to untracked moderation actions")


def capture_guild_does_not_exist_error(func: "WrapperInputFunc[P, T]") -> "WrapperOutputFunc[P, T]":  # noqa: E501
    """
    Decorator to send an error message to the Discord user when a GuildDoesNotExist is raised.

    The raised exception is then suppressed.
    """  # noqa: D401
    return ErrorCaptureDecorators.capture_error_and_close(
        func,
        error_type=GuildDoesNotExist,
        close_func=ErrorCaptureDecorators.critical_error_close_func
    )


def capture_strike_tracking_error(func: "WrapperInputFunc[P, T]") -> "WrapperOutputFunc[P, T]":
    """
    Decorator to send an error message to the user when a StrikeTrackingError is raised.

    The raised exception is then suppressed.
    """  # noqa: D401
    return ErrorCaptureDecorators.capture_error_and_close(
        func,
        error_type=StrikeTrackingError,
        close_func=ErrorCaptureDecorators.strike_tracking_error_close_func
    )
