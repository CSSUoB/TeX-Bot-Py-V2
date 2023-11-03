from cogs._utils import TeXBotApplicationContext
from exceptions import UserNotInCSSDiscordServer


class Checks:
    @staticmethod
    async def check_interaction_user_in_css_guild(ctx: TeXBotApplicationContext) -> bool:
        try:
            await ctx.bot.get_css_user(ctx.user)
        except UserNotInCSSDiscordServer:
            return False
        return True

    @staticmethod
    async def check_interaction_user_has_committee_role(ctx: TeXBotApplicationContext) -> bool:
        return await ctx.bot.check_user_has_committee_role(ctx.user)
