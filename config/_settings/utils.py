from collections.abc import Sequence

__all__: Sequence[str] = ("is_running_in_async", "get_settings_file_path")


import asyncio
import logging
import os
from logging import Logger
from typing import Final

from aiopath import AsyncPath

from config.constants import PROJECT_ROOT

logger: Final[Logger] = logging.getLogger("TeX-Bot")


async def get_settings_file_path() -> AsyncPath:
    settings_file_not_found_message: str = (
        "No settings file was found. "
        "Please make sure you have created a `tex-bot-deployment.yaml` file."
    )

    raw_settings_file_path: str | None = (
        os.getenv("TEX_BOT_SETTINGS_FILE_PATH", None)
        or os.getenv("TEX_BOT_SETTINGS_FILE", None)
        or os.getenv("TEX_BOT_SETTINGS_PATH", None)
        or os.getenv("TEX_BOT_SETTINGS", None)
        or os.getenv("TEX_BOT_CONFIG_FILE_PATH", None)
        or os.getenv("TEX_BOT_CONFIG_FILE", None)
        or os.getenv("TEX_BOT_CONFIG_PATH", None)
        or os.getenv("TEX_BOT_CONFIG", None)
        or os.getenv("TEX_BOT_DEPLOYMENT_FILE_PATH", None)
        or os.getenv("TEX_BOT_DEPLOYMENT_FILE", None)
        or os.getenv("TEX_BOT_DEPLOYMENT_PATH", None)
        or os.getenv("TEX_BOT_DEPLOYMENT", None)
    )

    if raw_settings_file_path:
        settings_file_not_found_message = (
            "A path to the settings file location was provided by environment variable, "
            "however this path does not refer to an existing file."
        )
    else:
        logger.debug(
            (
                "Settings file location not supplied by environment variable, "
                "falling back to `Tex-Bot-deployment.yaml`."
            ),
        )
        raw_settings_file_path = "tex-bot-deployment.yaml"
        if not await (AsyncPath(PROJECT_ROOT) / raw_settings_file_path).exists():
            raw_settings_file_path = "tex-bot-settings.yaml"

            if not await (AsyncPath(PROJECT_ROOT) / raw_settings_file_path).exists():
                raw_settings_file_path = "tex-bot-config.yaml"

    settings_file_path: AsyncPath = AsyncPath(raw_settings_file_path)

    if not await settings_file_path.is_file():
        raise FileNotFoundError(settings_file_not_found_message)

    return settings_file_path


def is_running_in_async() -> bool:
    """Determine whether the current context is asynchronous or not."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    else:
        return True
