"""Command check decorators to ensure given predicates before executing a command."""

__all__: Sequence[str] = ("CommandChecks",)

lazy from collections.abc import Awaitable, Callable, Sequence
lazy from typing import Concatenate

lazy from discord.ext import commands
lazy from discord.ext.commands import CheckFailure

lazy from exceptions import DiscordMemberNotInMainGuildError

lazy from .msl import msl_auth_cookie_is_set, msl_is_configured
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

        # NOTE: The check function shares this decorator's name, so that `is_interaction_user_in_main_guild_failure()` can identify it within a `CheckAnyFailure`
        async def check_interaction_user_in_main_guild(ctx: TeXBotApplicationContext) -> bool:
            try:
                await ctx.bot.get_main_guild_member(ctx.user)
            except DiscordMemberNotInMainGuildError:
                return False
            return True

        return commands.check_any(
            commands.check(
                check_interaction_user_in_main_guild  # type: ignore[arg-type]
            )
        )(func)

    @staticmethod
    def check_interaction_user_has_committee_role[T: TeXBotBaseCog, **P](
        func: Callable[Concatenate[T, P], Awaitable[None]],
    ) -> Callable[Concatenate[T, P], Awaitable[None]]:
        """
        Command check decorator to ensure the interaction user has the "Committee" role.

        If this check does not pass, the decorated command will not be executed.
        Instead, an error message will be sent to the user.
        """

        # NOTE: The check function shares this decorator's name, so that `is_interaction_user_has_committee_role_failure()` can identify it within a `CheckAnyFailure`
        async def check_interaction_user_has_committee_role(
            ctx: TeXBotApplicationContext,
        ) -> bool:
            return await ctx.bot.check_user_has_committee_role(ctx.user)

        return commands.check_any(
            commands.check(
                check_interaction_user_has_committee_role  # type: ignore[arg-type]
            )
        )(func)

    @staticmethod
    def check_msl_is_configured[T: TeXBotBaseCog, **P](
        func: Callable[Concatenate[T, P], Awaitable[None]],
    ) -> Callable[Concatenate[T, P], Awaitable[None]]:
        """
        Command check decorator to ensure that your group's MSL website can be accessed.

        Both the MSL organisation ID & the MSL authentication cookie must be set.
        If this check does not pass, the decorated command will not be executed.
        Instead, an error message will be sent to the user.
        """

        # NOTE: The check function shares this decorator's name, so that `is_msl_is_configured_failure()` can identify it within a `CheckAnyFailure`
        async def check_msl_is_configured(ctx: TeXBotApplicationContext) -> bool:  # noqa: ARG001
            return msl_is_configured()

        return commands.check_any(
            commands.check(
                check_msl_is_configured  # type: ignore[arg-type]
            )
        )(func)

    @staticmethod
    def check_msl_auth_cookie_is_set[T: TeXBotBaseCog, **P](
        func: Callable[Concatenate[T, P], Awaitable[None]],
    ) -> Callable[Concatenate[T, P], Awaitable[None]]:
        """
        Command check decorator to ensure that the SU platform access cookie is set.

        For commands that reach the SU platform without needing your group's MSL
        organisation ID. If this check does not pass, the decorated command will not be
        executed. Instead, an error message will be sent to the user.
        """

        # NOTE: The check function shares this decorator's name, so that `is_msl_auth_cookie_is_set_failure()` can identify it within a `CheckAnyFailure`
        async def check_msl_auth_cookie_is_set(ctx: TeXBotApplicationContext) -> bool:  # noqa: ARG001
            return msl_auth_cookie_is_set()

        return commands.check_any(
            commands.check(
                check_msl_auth_cookie_is_set  # type: ignore[arg-type]
            )
        )(func)

    @classmethod
    def is_interaction_user_in_main_guild_failure(cls, check: CheckFailure) -> bool:
        """Whether the check failed due to the user not being in your Discord guild."""
        return bool(check.__name__ == cls.check_interaction_user_in_main_guild.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_interaction_user_has_committee_role_failure(cls, check: CheckFailure) -> bool:
        """Whether the check failed due to the user not having the committee role."""
        return bool(check.__name__ == cls.check_interaction_user_has_committee_role.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_msl_is_configured_failure(cls, check: CheckFailure) -> bool:
        """Whether the check failed due to your group's MSL website not being set up."""
        return bool(check.__name__ == cls.check_msl_is_configured.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_msl_auth_cookie_is_set_failure(cls, check: CheckFailure) -> bool:
        """Whether the check failed due to the SU platform access cookie not being set."""
        return bool(check.__name__ == cls.check_msl_auth_cookie_is_set.__name__)  # type: ignore[attr-defined]
