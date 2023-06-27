import discord
from django.core import management

from config import settings
from utils import TeXBot

intents: discord.Intents = discord.Intents.default()
# noinspection PyDunderSlots,PyUnresolvedReferences
intents.members = True

bot = TeXBot(intents=intents)

cog: str
for cog in {"events", "commands", "tasks"}:
    bot.load_extension(f"cogs.{cog}")

if __name__ == "__main__":
    management.call_command("makemigrations")
    management.call_command("makemigrations", "core")
    management.call_command("migrate")
    bot.run(settings["DISCORD_BOT_TOKEN"])
