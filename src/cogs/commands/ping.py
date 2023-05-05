import logging
import random

from discord import ApplicationContext, Bot
from discord.ext import commands

from src.utils import settings


class Ping(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @commands.slash_command(description="Replies with Pong!")
    async def ping(self, ctx: ApplicationContext):
        logging.warning(f"{ctx.interaction.user} made me pong!!")
        await ctx.respond(random.choices([
            "Pong!",
            "64 bytes from TeX: icmp_seq=1 ttl=63 time=0.01 ms"
        ], weights=settings["PING_COMMAND_EASTER_EGG_WEIGHTS"])[0])


def setup(bot: Bot):
    bot.add_cog(Ping(bot))
