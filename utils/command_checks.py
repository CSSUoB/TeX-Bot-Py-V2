"""Command check decorators to ensure given predicates before executing a command."""

from typing import TYPE_CHECKING

from discord.ext import commands

from exceptions import DiscordMemberNotInMainGuildError

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from discord.ext.commands import CheckFailure
    from discord.ext.commands.context import Context

    from utils.tex_bot import TeXBot


__all__: "Sequence[str]" = ("CommandChecks",)


class CommandChecks:
    """Command check decorators to ensure given predicates before executing a command."""

    @staticmethod
    def check_interaction_user_in_main_guild[T](
        func: "Callable[[T], T]",
    ) -> "Callable[[T], T]":
        """
        Decorator to ensure the interaction user of a command is within your group's Discord guild.

        If this check does not pass, the decorated command will not be executed.
        Instead an error message will be sent to the user.
        """  # noqa: D401

        async def _check(ctx: "Context[TeXBot]") -> bool:
            try:
                await ctx.bot.get_main_guild_member(ctx.user)
            except DiscordMemberNotInMainGuildError:
                return False
            return True

        return commands.check_any(commands.check(_check))(func)

    @staticmethod
    def check_interaction_user_has_committee_role[T](
        func: "Callable[[T], T]",
    ) -> "Callable[[T], T]":
        """
        Command check decorator to ensure the interaction user has the "Committee" role.

        If this check does not pass, the decorated command will not be executed.
        Instead, an error message will be sent to the user.
        """

        async def _check(ctx: "Context[TeXBot]") -> bool:
            return await ctx.bot.check_user_has_committee_role(ctx.user)

        return commands.check_any(commands.check(_check))(func)

    @classmethod
    def is_interaction_user_in_main_guild_failure(cls, check: "CheckFailure") -> bool:
        # noinspection GrazieInspection
        """Whether check failed due to the interaction user not being in your Discord guild."""
        return bool(check.__name__ == cls._check_interaction_user_in_main_guild.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_interaction_user_has_committee_role_failure(cls, check: "CheckFailure") -> bool:
        # noinspection GrazieInspection
        """Whether check failed due to the interaction user not having the committee role."""
        return bool(check.__name__ == cls._check_interaction_user_has_committee_role.__name__)  # type: ignore[attr-defined]
