"""Helpers for re-applying changed configuration settings to running background tasks."""

import logging
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import datetime
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = ("RestartableTask", "reapply_task_settings")


class RestartableTask(Protocol):
    """
    The parts of a `discord.ext.tasks.Loop` needed to re-apply its settings.

    NOTE: Declared structurally, rather than referring to `Loop` itself, because `Loop`
    is generic over a callable returning `Any`, which cannot be named under this
    project's type-checking settings.
    """

    def is_running(self) -> bool:
        """Whether this task is currently running."""

    def cancel(self) -> None:
        """Stop this task, without waiting for its current iteration to finish."""

    def start(self, *args: object, **kwargs: object) -> object:
        """Begin running this task."""

    def restart(self, *args: object, **kwargs: object) -> None:
        """Stop this task, then begin running it again."""

    def change_interval(self, *, seconds: float) -> None:
        """Change how long this task waits between iterations."""


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


def reapply_task_settings(
    task: RestartableTask,
    *,
    changed_settings: "AbstractSet[str]",
    enabled: bool,
    enabled_setting_name: str | None,
    interval: "datetime.timedelta",
    interval_setting_name: str,
) -> None:
    """
    Apply any changed enabled-flag or interval setting to the given background task.

    Pass `enabled_setting_name=None` where whether the task runs cannot be changed
    without a restart; only its interval is then re-applied.

    A task's interval is captured when its cog class is defined, so (unlike most
    settings) it does not follow the loaded configuration by itself and must be
    re-applied here.

    Changing the interval of an already-running task would otherwise only take effect
    once its current wait had elapsed, which for a multi-hour interval could be long
    after the change was made, so the task is restarted to apply it immediately.
    """
    ENABLED_CHANGED: Final[bool] = (
        enabled_setting_name is not None and enabled_setting_name in changed_settings
    )
    INTERVAL_CHANGED: Final[bool] = interval_setting_name in changed_settings

    if not ENABLED_CHANGED and not INTERVAL_CHANGED:
        return

    if ENABLED_CHANGED and not enabled:
        if task.is_running():
            task.cancel()
            logger.debug("Stopped the task controlled by %r.", enabled_setting_name)
        return

    if INTERVAL_CHANGED:
        task.change_interval(seconds=interval.total_seconds())
        logger.debug("Changed %r to %s.", interval_setting_name, interval)

    if not task.is_running():
        _ = task.start()
        logger.debug("Started the task controlled by %r.", enabled_setting_name)
        return

    if INTERVAL_CHANGED:
        task.restart()
