"""Command check decorators to ensure given predicates before executing a command."""

from typing import TYPE_CHECKING

from discord.ext import commands

from exceptions import DiscordMemberNotInMainGuildError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence
    from typing import Concatenate

    from discord.ext.commands import CheckFailure

    from .tex_bot_base_cog import TeXBotBaseCog
    from .tex_bot_contexts import TeXBotApplicationContext

__all__: "Sequence[str]" = ("CommandChecks",)


class CommandChecks:
    """Command check decorators to ensure given predicates before executing a command."""

    @staticmethod
    def check_interaction_user_in_main_guild[T: TeXBotBaseCog, **P](
        func: "Callable[Concatenate[T, P], Awaitable[None]]",
    ) -> "Callable[Concatenate[T, P], Awaitable[None]]":
        """
        Decorator to ensure the interaction user of a command is in your group's Discord guild.

        If this check does not pass, the decorated command will not be executed.
        Instead an error message will be sent to the user.
        """  # noqa: D401

        async def _check(ctx: "TeXBotApplicationContext") -> bool:
            try:
                await ctx.bot.get_main_guild_member(ctx.user)
            except DiscordMemberNotInMainGuildError:
                return False
            return True

        return commands.check_any(
            commands.check(
                _check  # type: ignore[arg-type]
            )
        )(func)

    @staticmethod
    def check_interaction_user_has_committee_role[T: TeXBotBaseCog, **P](
        func: "Callable[Concatenate[T, P], Awaitable[None]]",
    ) -> "Callable[Concatenate[T, P], Awaitable[None]]":
        """
        Command check decorator to ensure the interaction user has the "Committee" role.

        If this check does not pass, the decorated command will not be executed.
        Instead, an error message will be sent to the user.
        """

        async def _check(ctx: "TeXBotApplicationContext") -> bool:
            return await ctx.bot.check_user_has_committee_role(ctx.user)

        return commands.check_any(
            commands.check(
                _check  # type: ignore[arg-type]
            )
        )(func)

    @staticmethod
    def check_interation_user_has_committee_or_elect_role[T: TeXBotBaseCog, **P](
        func: "Callable[Concatenate[T, P], Awaitable[None]]",
    ) -> "Callable[Concatenate[T, P], Awaitable[None]]":
        async def _check(ctx: "TeXBotApplicationContext") -> bool:
            return await ctx.bot.check_user_has_committee_or_elect_role(ctx.user)

        return commands.check_any(
            commands.check(
                _check  # type: ignore[arg-type]
            )
        )(func)

    @classmethod
    def is_interaction_user_in_main_guild_failure(cls, check: "CheckFailure") -> bool:
        """Whether the check failed due to the user not being in your Discord guild."""
        return bool(check.__name__ == cls._check_interaction_user_in_main_guild.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_interaction_user_has_committee_role_failure(cls, check: "CheckFailure") -> bool:
        """Whether the check failed due to the user not having the committee role."""
        return bool(check.__name__ == cls._check_interaction_user_has_committee_role.__name__)  # type: ignore[attr-defined]
