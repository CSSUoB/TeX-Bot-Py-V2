"""Utility classes used for the cogs section of this project."""

import discord
from discord import Cog

from utils import TeXBot


class TeXBotCog(Cog):
    """Base Cog subclass that stores a reference to the currently running bot."""

    def __init__(self, bot: TeXBot) -> None:
        """Initialize a new cog instance, storing a reference to the bot object."""
        self.bot: TeXBot = bot


class TeXBotAutocompleteContext(discord.AutocompleteContext):
    """
    Type-hinting class overriding AutocompleteContext's reference to the Bot class.

    Pycord's default AutocompleteContext references the standard discord.Bot class,
    but cogs require a reference to the TeXBot class, so this AutocompleteContext subclass
    should be used in cogs instead.
    """

    bot: TeXBot
