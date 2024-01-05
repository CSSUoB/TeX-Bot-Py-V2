"""
The main entrypoint into the running of the bot.

It loads the settings values from the .env file/the environment variables,
then ensures the Django database is correctly migrated to the latest version and finally begins
the asynchronous running process for the Discord bot.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ("bot",)


import discord

import config
from config import settings
from utils import SuppressTraceback, TeXBot

with SuppressTraceback():
    config.run_setup()
    intents: discord.Intents = discord.Intents.default()
    # noinspection PyDunderSlots,PyUnresolvedReferences
    intents.members = True

    bot = TeXBot(intents=intents)

bot.load_extension("cogs")

if __name__ == "__main__":
    bot.run(settings["DISCORD_BOT_TOKEN"])
