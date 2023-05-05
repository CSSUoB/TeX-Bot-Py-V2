import discord

from src.utils import settings


bot = discord.Bot(debug_guilds=[settings["DISCORD_GUILD_ID"]])


cogs_list = {
    "events"
}
cog: str
for cog in cogs_list:
    bot.load_extension(f"cogs.{cog}")


if __name__ == '__main__':
    bot.run(settings["DISCORD_BOT_TOKEN"])
