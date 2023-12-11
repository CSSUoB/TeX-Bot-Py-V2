"""
The main entrypoint into the running of the bot.

It loads the settings values from the .env file/the environment variables,
then ensures the Django database is correctly migrated to the latest version and finally begins
the asynchronous running process for the Discord bot.
"""

import discord
from django.core import management

import config
from config import settings
from utils import SuppressTraceback, TeXBot

with SuppressTraceback():
    config.setup_env_variables()
    config.setup_django()

    intents: discord.Intents = discord.Intents.default()
    # noinspection PyDunderSlots,PyUnresolvedReferences
    intents.members = True

    bot = TeXBot(intents=intents)

bot.load_extension("cogs")

if __name__ == "__main__":
    with SuppressTraceback():
        management.call_command("migrate")

    bot.run(settings["DISCORD_BOT_TOKEN"])
