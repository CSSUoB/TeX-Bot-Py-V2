"""Command check decorators to ensure given predicates before executing a command."""

__all__: Sequence[str] = ("CommandChecks",)

lazy from collections.abc import Awaitable, Callable, Sequence
lazy from typing import Concatenate

lazy from discord.ext import commands
lazy from discord.ext.commands import CheckFailure

lazy from exceptions import DiscordMemberNotInMainGuildError

lazy from .tex_bot_base_cog import TeXBotBaseCog
lazy from .tex_bot_contexts import TeXBotApplicationContext


class CommandChecks:
    """Command check decorators to ensure given predicates before executing a command."""

    @staticmethod
    def check_interaction_user_in_main_guild[T: TeXBotBaseCog, **P](
        func: Callable[Concatenate[T, P], Awaitable[None]],
    ) -> Callable[Concatenate[T, P], Awaitable[None]]:
        """
        Decorator to ensure the interaction user of a command is in your group's Discord guild.

        If this check does not pass, the decorated command will not be executed.
        Instead, an error message will be sent to the user.
        """  # noqa: D401

        async def _check(ctx: TeXBotApplicationContext) -> bool:
            try:
                await ctx.bot.get_main_guild_member(ctx.user)
            except DiscordMemberNotInMainGuildError:
                return False
            return True

        return commands.check_any(commands.check(_check))(func)  # type: ignore[arg-type]

    @staticmethod
    def check_interaction_user_has_committee_role[T: TeXBotBaseCog, **P](
        func: Callable[Concatenate[T, P], Awaitable[None]],
    ) -> Callable[Concatenate[T, P], Awaitable[None]]:
        """
        Command check decorator to ensure the interaction user has the "Committee" role.

        If this check does not pass, the decorated command will not be executed.
        Instead, an error message will be sent to the user.
        """

        async def _check(ctx: TeXBotApplicationContext) -> bool:
            return await ctx.bot.check_user_has_committee_role(ctx.user)

        return commands.check_any(commands.check(_check))(func)  # type: ignore[arg-type]

    @classmethod
    def is_interaction_user_in_main_guild_failure(cls, check: CheckFailure) -> bool:
        """Whether the check failed due to the user not being in your Discord guild."""
        return bool(check.__name__ == cls.check_interaction_user_in_main_guild.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_interaction_user_has_committee_role_failure(cls, check: CheckFailure) -> bool:
        """Whether the check failed due to the user not having the committee role."""
        return bool(check.__name__ == cls.check_interaction_user_has_committee_role.__name__)  # type: ignore[attr-defined]
