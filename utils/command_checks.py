from collections.abc import Callable

from discord.ext import commands
from discord.ext.commands import CheckFailure
# noinspection PyProtectedMember
from discord.ext.commands.core import T

from exceptions import UserNotInCSSDiscordServer
from utils.tex_bot_contexts import TeXBotApplicationContext


class CommandChecks:
    @staticmethod
    async def _check_interaction_user_in_css_guild(ctx: TeXBotApplicationContext) -> bool:
        try:
            await ctx.bot.get_css_user(ctx.user)
        except UserNotInCSSDiscordServer:
            return False
        return True

    check_interaction_user_in_css_guild: Callable[[T], T]

    @staticmethod
    async def _check_interaction_user_has_committee_role(ctx: TeXBotApplicationContext) -> bool:  # noqa: E501
        return await ctx.bot.check_user_has_committee_role(ctx.user)

    check_interaction_user_has_committee_role: Callable[[T], T]

    @classmethod
    def is_interaction_user_in_css_guild_failure(cls, check: CheckFailure) -> bool:
        return bool(check.__name__ == cls._check_interaction_user_in_css_guild.__name__)  # type: ignore[attr-defined]

    @classmethod
    def is_interaction_user_has_committee_role_failure(cls, check: CheckFailure) -> bool:
        return bool(check.__name__ == cls._check_interaction_user_has_committee_role.__name__)  # type: ignore[attr-defined]


# noinspection PyProtectedMember
CommandChecks.check_interaction_user_in_css_guild = commands.check_any(
    commands.check(CommandChecks._check_interaction_user_in_css_guild)  # type: ignore[arg-type] # noqa: SLF001
)
# noinspection PyProtectedMember
CommandChecks.check_interaction_user_has_committee_role = commands.check_any(
    commands.check(CommandChecks._check_interaction_user_has_committee_role)  # type: ignore[arg-type] # noqa: SLF001
)
