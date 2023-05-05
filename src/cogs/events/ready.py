import logging

from discord import Bot
from discord.ext import commands


class Ready(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"Ready! Logged in as {self.bot.user}")


def setup(bot: Bot):
    bot.add_cog(Ready(bot))
