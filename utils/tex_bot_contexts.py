"""
Type-hinting classes that override the Pycord Context classes.

These custom, overridden classes contain a reference to the custom bot class TeXBot,
rather than Pycord's default Bot class.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ("TeXBotAutocompleteContext", "TeXBotApplicationContext")


import abc
from typing import final, override

import discord

from .tex_bot import TeXBot


class _TeXBotContextMixin(abc.ABC):  # noqa: B024
    @override
    def __init__(self, tex_bot: TeXBot, interaction: discord.Interaction) -> None:
        self._tex_bot: TeXBot = tex_bot

        super().__init__(tex_bot, interaction)  # type: ignore[call-arg]

    @property
    def tex_bot(self) -> TeXBot:
        return self._tex_bot

    @property  # type: ignore[misc]
    @final
    def bot(self) -> discord.Bot:
        raise DeprecationWarning

    @bot.setter
    @final
    def bot(self, __value: discord.Bot, /) -> None:
        raise DeprecationWarning


class TeXBotAutocompleteContext(_TeXBotContextMixin, discord.AutocompleteContext):  # type: ignore[misc]
    """
    Type-hinting class overriding AutocompleteContext's reference to the Bot class.

    Pycord's default AutocompleteContext references Pycord's standard Bot class,
    but cogs require a reference to the TeXBot class, so this AutocompleteContext subclass
    should be used in cogs instead.
    """


class TeXBotApplicationContext(_TeXBotContextMixin, discord.ApplicationContext):  # type: ignore[misc]
    """
    Type-hinting class overriding ApplicationContext's reference to the Bot class.

    Pycord's default ApplicationContext references Pycord's standard Bot class,
    but cogs require a reference to the TeXBot class, so this ApplicationContext subclass
    should be used in cogs instead.
    """
