import discord

from utils.tex_bot import TeXBot


class TeXBotAutocompleteContext(discord.AutocompleteContext):
    """
    Type-hinting class overriding AutocompleteContext's reference to the Bot class.

    Pycord's default AutocompleteContext references the standard discord.Bot class,
    but cogs require a reference to the TeXBot class, so this AutocompleteContext subclass
    should be used in cogs instead.
    """

    bot: TeXBot


class TeXBotApplicationContext(discord.ApplicationContext):
    """
    Type-hinting class overriding ApplicationContext's reference to the Bot class.

    Pycord's default ApplicationContext references the standard discord.Bot class,
    but cogs require a reference to the TeXBot class, so this ApplicationContext subclass
    should be used in cogs instead.
    """

    bot: TeXBot
