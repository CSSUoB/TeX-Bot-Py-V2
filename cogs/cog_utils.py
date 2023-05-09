from discord.ext.commands import Cog

from utils import TeXBot


class Bot_Cog(Cog):
    def __init__(self, bot: TeXBot):
        self.bot: TeXBot = bot
