"""
Common decorator utilities to capture & suppress errors.

Capturing errors is necessary in contexts where exceptions are not already suppressed.
"""

import functools
import logging
from typing import TYPE_CHECKING

from exceptions import GuildDoesNotExistError, StrikeTrackingError

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Sequence
    from logging import Logger
    from typing import Concatenate, Final

    from .tex_bot_base_cog import TeXBotBaseCog

__all__: Sequence[str] = (
    "ErrorCaptureDecorators",
    "capture_guild_does_not_exist_error",
    "capture_strike_tracking_error",
)


if TYPE_CHECKING:
    type WrapperInputFunc[**P, T_ret] = (
        Callable[Concatenate[TeXBotBaseCog, P], Coroutine[object, object, T_ret]]
        | Callable[P, Coroutine[object, object, T_ret]]
    )
    type WrapperOutputFunc[**P, T_ret] = Callable[P, Coroutine[object, object, T_ret | None]]
    type DecoratorInputFunc[**P, T_cog: TeXBotBaseCog, T_ret] = Callable[
        Concatenate[T_cog, P], Coroutine[object, object, T_ret]
    ]

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class ErrorCaptureDecorators:
    """
    Common decorator utilities to capture & suppress errors.

    Capturing errors is necessary in contexts where exceptions are not already suppressed.
    """

    @staticmethod
    def capture_error_and_close[**P, T_ret, T_cog: TeXBotBaseCog](
        func: DecoratorInputFunc[P, T_cog, T_ret],
        error_type: type[BaseException],
        close_func: Callable[[BaseException], None],
    ) -> WrapperOutputFunc[P, T_ret]:
        """
        Decorator to send an error message to the user when the given exception type is raised.

        The raised exception is then suppressed.
        """  # noqa: D401

        @functools.wraps(func)
        async def wrapper(self: T_cog, /, *args: P.args, **kwargs: P.kwargs) -> T_ret | None:  # type: ignore[misc]  # noqa: CAR150
            try:
                return await func(self, *args, **kwargs)
            except error_type as error:
                close_func(error)
                await self.bot.close()

        return wrapper  # type: ignore[return-value]

    @staticmethod
    def critical_error_close_func(error: BaseException) -> None:
        """Component function to send logging messages when a critical error is encountered."""
        logger.critical(str(error).rstrip(".:"))

    @classmethod
    def strike_tracking_error_close_func(cls, error: BaseException) -> None:
        """Component function to send logging messages when a StrikeTrackingError is raised."""
        cls.critical_error_close_func(error)
        logger.warning("Critical errors are likely to lead to untracked moderation actions")


def capture_guild_does_not_exist_error[**P, T_ret](
    func: WrapperInputFunc[P, T_ret],
) -> WrapperOutputFunc[P, T_ret]:
    """
    Decorator to send an error message to the Discord user when a GuildDoesNotExist is raised.

    The raised exception is then suppressed.
    """  # noqa: D401
    return ErrorCaptureDecorators.capture_error_and_close(
        func,  # type: ignore[arg-type]
        error_type=GuildDoesNotExistError,
        close_func=ErrorCaptureDecorators.critical_error_close_func,
    )


def capture_strike_tracking_error[**P, T_ret](
    func: WrapperInputFunc[P, T_ret],
) -> WrapperOutputFunc[P, T_ret]:
    """
    Decorator to send an error message to the user when a StrikeTrackingError is raised.

    The raised exception is then suppressed.
    """  # noqa: D401
    return ErrorCaptureDecorators.capture_error_and_close(
        func,  # type: ignore[arg-type]
        error_type=StrikeTrackingError,
        close_func=ErrorCaptureDecorators.strike_tracking_error_close_func,
    )
