"""
Type-hinting classes that override the Pycord Context classes.

These custom, overridden classes contain a reference to the custom bot class TeXBot,
rather than Pycord's default Bot class.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ("TeXBotAutocompleteContext", "TeXBotApplicationContext")


import discord

from utils.tex_bot import TeXBot


class TeXBotAutocompleteContext(discord.AutocompleteContext):
    """
    Type-hinting class overriding AutocompleteContext's reference to the Bot class.

    Pycord's default AutocompleteContext references Pycord's standard Bot class,
    but cogs require a reference to the TeXBot class, so this AutocompleteContext subclass
    should be used in cogs instead.
    """

    bot: TeXBot


class TeXBotApplicationContext(discord.ApplicationContext):
    """
    Type-hinting class overriding ApplicationContext's reference to the Bot class.

    Pycord's default ApplicationContext references Pycord's standard Bot class,
    but cogs require a reference to the TeXBot class, so this ApplicationContext subclass
    should be used in cogs instead.
    """

    bot: TeXBot
