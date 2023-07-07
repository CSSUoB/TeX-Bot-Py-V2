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
    management.call_command("makemigrations")
    management.call_command("migrate")

    del sys.tracebacklimit

    bot.run(settings["DISCORD_BOT_TOKEN"])
