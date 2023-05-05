import logging

from discord import ApplicationContext, Bot
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @commands.slash_command(description="Replies with Pong!")
    async def ping(self, ctx: ApplicationContext):
        logging.warning(f"{ctx.interaction.user} made me pong!!")
        await ctx.respond("Pong!")


def setup(bot: Bot):
    bot.add_cog(Ping(bot))
