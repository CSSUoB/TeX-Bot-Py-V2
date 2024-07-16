#!/usr/bin/env python
"""
The main entrypoint into the running of TeX-Bot.

It loads the settings values from the .env file/the environment variables,
then ensures the Django database is correctly migrated to the latest version and finally begins
the asynchronous running process for TeX-Bot.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ("tex_bot",)


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

    tex_bot: TeXBot = TeXBot(intents=intents)

    tex_bot.load_extension("cogs")


def _run_tex_bot() -> NoReturn:
    tex_bot.run(settings["DISCORD_BOT_TOKEN"])

    if tex_bot.EXIT_WAS_DUE_TO_KILL_COMMAND:
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    _run_tex_bot()
