"""
    Utility classes used for the cogs section of this project.
"""

import discord
from discord import Cog

from utils import TeXBot


class TeXBotCog(Cog):
    """
        Base Cog class that inherits from Pycord's default Cog class but
        provides the functionality to store a reference to the currently running
        bot.
    """

    def __init__(self, bot: TeXBot):
        self.bot: TeXBot = bot


class TeXBotAutocompleteContext(discord.AutocompleteContext):
    """
        Overrides the type-hinting of Pycord's default AutocompleteContext class
        so that the bot attribute references the TeXBot class, rather than
        Pycord's default Bot class.
    """

    bot: TeXBot
