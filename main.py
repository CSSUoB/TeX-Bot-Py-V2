"""
The main entrypoint into the running of the bot.

It loads the settings values from the .env file/the environment variables,
then ensures the Django database is correctly migrated to the latest version and finally begins
the asynchronous running process for the Discord bot.
"""

import sys

import discord
from django.core import management

import config
from config import settings
from utils import TeXBot

# noinspection SpellCheckingInspection
sys.tracebacklimit = 0

config.setup_env_variables()
config.setup_django()

intents: discord.Intents = discord.Intents.default()
# noinspection PyDunderSlots,PyUnresolvedReferences
intents.members = True

bot = TeXBot(intents=intents)

cog: str
for cog in {"events", "commands", "tasks"}:
    bot.load_extension(f"cogs.{cog}")

if __name__ == "__main__":
    management.call_command("migrate")

    del sys.tracebacklimit

    bot.run(settings["DISCORD_BOT_TOKEN"])
