"""Command check decorators to ensure given predicates before executing a command."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommandChecks",)


from collections.abc import Callable
from typing import Final

import discord
from discord.ext import commands

# noinspection PyProtectedMember
from discord.ext.commands.core import T

from exceptions import DiscordMemberNotInMainGuildError
from utils.tex_bot_contexts import TeXBotApplicationContext


class CommandChecks:
    """Command check decorators to ensure given predicates before executing a command."""

    @staticmethod
    async def _check_interaction_user_in_main_guild(ctx: TeXBotApplicationContext) -> bool:
        try:
            await ctx.bot.get_main_guild_member(ctx.user)
        except DiscordMemberNotInMainGuildError:
            return False
        return True

    check_interaction_user_in_main_guild: Callable[[T], T]
    """
    Decorator to ensure the interaction user of a command is within your group's Discord guild.

    If this check does not pass, the decorated command will not be executed.
    Instead an error message will be sent to the user.
    """

    @staticmethod
    async def _check_interaction_user_has_committee_role(ctx: TeXBotApplicationContext) -> bool:  # noqa: E501
        return await ctx.bot.check_user_has_committee_role(ctx.user)

    check_interaction_user_has_committee_role: Callable[[T], T]
    """
    Command check decorator to ensure the interaction user has the "Committee" role.

    If this check does not pass, the decorated command will not be executed.
    Instead an error message will be sent to the user.
    """

    @classmethod
    def _compare_check_failure(cls, check: Callable[[discord.ApplicationContext], bool], interaction_name: str) -> bool:  # noqa: E501
        check_name: str | None = getattr(check, "__name__", None)
        if check_name is None:
            COULD_NOT_CONFIRM_INTERACTION_MESSAGE: Final[str] = (
                "Could not confirm interaction type. Check's name did not exist."
            )
            raise ValueError(COULD_NOT_CONFIRM_INTERACTION_MESSAGE)

        return bool(check.__name__ == interaction_name)

    @classmethod
    def is_interaction_user_in_main_guild_failure(cls, check: Callable[[discord.ApplicationContext], bool]) -> bool:  # noqa: E501
        # noinspection GrazieInspection
        """Whether check failed due to the interaction user not being in your Discord guild."""
        return cls._compare_check_failure(
            check,
            cls._check_interaction_user_in_main_guild.__name__,
        )

    @classmethod
    def is_interaction_user_has_committee_role_failure(cls, check: Callable[[discord.ApplicationContext], bool]) -> bool:  # noqa: E501
        # noinspection GrazieInspection
        """Whether check failed due to the interaction user not having the committee role."""
        return cls._compare_check_failure(
            check,
            cls._check_interaction_user_has_committee_role.__name__,
        )


# noinspection PyProtectedMember
CommandChecks.check_interaction_user_in_main_guild = commands.check_any(
    commands.check(CommandChecks._check_interaction_user_in_main_guild),  # noqa: SLF001
)

# noinspection PyProtectedMember
CommandChecks.check_interaction_user_has_committee_role = commands.check_any(
    commands.check(CommandChecks._check_interaction_user_has_committee_role),  # noqa: SLF001
)
