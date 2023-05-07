import discord
from discord import Guild, Role, TextChannel

from exceptions import ChannelDoesNotExist, GuildDoesNotExist, RoleDoesNotExist
from setup import settings


class TeXBot(discord.Bot):
    def __init__(self, *args, **kwargs):
        self._css_guild: Guild | None = None
        self._committee_role: Role | None = None
        self._roles_channel: TextChannel | None = None

        super().__init__(*args, **kwargs)

    @property
    def css_guild(self) -> Guild:
        if self._css_guild is None:
            raise GuildDoesNotExist()

        return self._css_guild

    @property
    def committee_role(self) -> Role:
        if self._committee_role is None:
            raise RoleDoesNotExist()

        return self._committee_role

    @property
    def roles_channel(self) -> TextChannel:
        if self._roles_channel is None:
            raise ChannelDoesNotExist()

        return self._roles_channel


bot = TeXBot()


cogs_list = {
    "events",
    "commands"
}
cog: str
for cog in cogs_list:
    bot.load_extension(f"cogs.{cog}")


if __name__ == "__main__":
    bot.run(settings["DISCORD_BOT_TOKEN"])
