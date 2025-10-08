#!/usr/bin/env python
"""
The main entrypoint into the running of TeX-Bot.

It loads the settings values from the .env file/the environment variables,
then ensures the Django database is correctly migrated to the latest version and finally begins
the asynchronous running process for TeX-Bot.
"""

from typing import TYPE_CHECKING

import discord

import config
from config import settings
from utils import SuppressTraceback, TeXBot

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import NoReturn

__all__: Sequence[str] = ("bot",)

with SuppressTraceback():
    config.run_setup()

    bot: TeXBot = TeXBot(
        intents=discord.Intents.default() | discord.Intents.members
    )  # NOTE: See https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/261

    bot.load_extension("cogs")


def _run_bot() -> NoReturn:  # NOTE: See https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/261
    bot.run(settings["DISCORD_BOT_TOKEN"])

    raise SystemExit(0 if bot.EXIT_WAS_DUE_TO_KILL_COMMAND else 1)


if __name__ == "__main__":
    _run_bot()
