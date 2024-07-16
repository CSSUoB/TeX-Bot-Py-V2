"""Command check decorators to ensure given predicates before executing a command."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommandChecks",)


from collections.abc import Callable

from discord.ext import commands
from discord.ext.commands import CheckFailure

# noinspection PyProtectedMember
from discord.ext.commands.core import T

from exceptions import DiscordMemberNotInMainGuildError
from utils.tex_bot_contexts import TeXBotApplicationContext


class CommandChecks:
    """Command check decorators to ensure given predicates before executing a command."""

    @staticmethod
    async def _check_interaction_user_in_main_guild(ctx: TeXBotApplicationContext) -> bool:
        try:
            await ctx.tex_bot.get_main_guild_member(ctx.user)
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
        return await ctx.tex_bot.check_user_has_committee_role(ctx.user)

    check_interaction_user_has_committee_role: Callable[[T], T]
    """
    Command check decorator to ensure the interaction user has the "Committee" role.

    If this check does not pass, the decorated command will not be executed.
    Instead an error message will be sent to the user.
    """

    @classmethod
    def is_interaction_user_in_main_guild_failure(cls, check: CheckFailure) -> bool:
        # noinspection GrazieInspection
        """Whether check failed due to the interaction user not being in your Discord guild."""
        return bool(check.__name__ == cls._check_interaction_user_in_main_guild.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_interaction_user_has_committee_role_failure(cls, check: CheckFailure) -> bool:
        # noinspection GrazieInspection
        """Whether check failed due to the interaction user not having the committee role."""
        return bool(check.__name__ == cls._check_interaction_user_has_committee_role.__name__)  # type: ignore[attr-defined]


# noinspection PyProtectedMember
CommandChecks.check_interaction_user_in_main_guild = commands.check_any(
    commands.check(CommandChecks._check_interaction_user_in_main_guild),  # type: ignore[arg-type] # noqa: SLF001
)
# noinspection PyProtectedMember
CommandChecks.check_interaction_user_has_committee_role = commands.check_any(
    commands.check(CommandChecks._check_interaction_user_has_committee_role),  # type: ignore[arg-type] # noqa: SLF001
)
