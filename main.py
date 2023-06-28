import discord
from django.core import management

import config
from config import Settings
from utils import TeXBot

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

    bot.run(Settings["DISCORD_BOT_TOKEN"])
