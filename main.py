#!/usr/bin/env python
"""
The main entrypoint into the running of TeX-Bot.

It loads the settings values from the .env file/the environment variables,
then ensures the Django database is correctly migrated to the latest version and finally begins
the asynchronous running process for TeX-Bot.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ("bot",)


from typing import NoReturn

import discord

import config
from config import settings
from utils import SuppressTraceback, TeXBot

with SuppressTraceback():
    config.run_setup()

    intents: discord.Intents = discord.Intents.default()
    # noinspection PyDunderSlots,PyUnresolvedReferences
    intents.members = True

    # NOTE: The variable name `bot` is used here for consistency.
    # NOTE: `tex_bot` would be preferred but would be inconsitent with the required attribute name of Pycord's context classes
    # NOTE: See https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/261
    bot: TeXBot = TeXBot(intents=intents)

    bot.load_extension("cogs")


# NOTE: The function name `_run_bot()` is used here for consistency.
# NOTE: `_run_tex_bot()` would be preferred but would be inconsitent with the required attribute name of Pycord's context classes
# NOTE: See https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/261
def _run_bot() -> NoReturn:
    bot.run(settings["DISCORD_BOT_TOKEN"])

    if bot.EXIT_WAS_DUE_TO_KILL_COMMAND:
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    _run_bot()
