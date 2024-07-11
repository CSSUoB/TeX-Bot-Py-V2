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
from utils import SuppressTraceback, TeXBot, TeXBotExitReason

with SuppressTraceback():
    config.run_setup()

    intents: discord.Intents = discord.Intents.default()
    # noinspection PyDunderSlots,PyUnresolvedReferences
    intents.members = True

    bot: TeXBot = TeXBot(intents=intents)

    bot.load_extension("cogs")


def _run_tex_bot() -> NoReturn:
    bot.run(settings["DISCORD_BOT_TOKEN"])

    if bot.EXIT_REASON is TeXBotExitReason.RESTART_REQUIRED_DUE_TO_CHANGED_CONFIG:
        with SuppressTraceback():
            bot.reset_exit_reason()
            config.run_setup()
            bot.reload_extension("cogs")
            _run_tex_bot()

    raise SystemExit(bot.EXIT_REASON.value)


if __name__ == "__main__":
    _run_tex_bot()
