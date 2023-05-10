from discord import Intents

from setup import settings
from utils import TeXBot

intents: Intents = Intents.default()
# noinspection PyDunderSlots,PyUnresolvedReferences
intents.members = True

bot = TeXBot(intents=intents)

cog: str
for cog in {"events", "commands", "tasks"}:
    bot.load_extension(f"cogs.{cog}")

if __name__ == "__main__":
    bot.run(settings["DISCORD_BOT_TOKEN"])
