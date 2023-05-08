import discord
from discord import Guild, Intents, Role, TextChannel

from exceptions import CommitteeRoleDoesNotExist, GeneralChannelDoesNotExist, GuestRoleDoesNotExist, GuildDoesNotExist, RolesChannelDoesNotExist
from setup import settings


class TeXBot(discord.Bot):
    def __init__(self, *args, **kwargs):
        self._css_guild: Guild | None = None
        self._committee_role: Role | None = None
        self._guest_role: Role | None = None
        self._roles_channel: TextChannel | None = None
        self._general_channel: TextChannel | None = None

        super().__init__(*args, **kwargs)

    @property
    def css_guild(self) -> Guild:
        if self._css_guild is None or discord.utils.get(self.guilds, id=settings["DISCORD_GUILD_ID"]) is None:
            raise GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"])

        return self._css_guild

    @property
    def committee_role(self) -> Role:
        if self._committee_role is None or discord.utils.get(self.css_guild.roles, id=self._committee_role.id) is None:
            raise CommitteeRoleDoesNotExist()

        return self._committee_role

    @property
    def guest_role(self) -> Role:
        if self._guest_role is None or discord.utils.get(self.css_guild.roles, id=self._guest_role.id) is None:
            raise GuestRoleDoesNotExist()

        return self._guest_role

    @property
    def roles_channel(self) -> TextChannel:
        if self._roles_channel is None or discord.utils.get(self.css_guild.text_channels, id=self._roles_channel.id) is None:
            raise RolesChannelDoesNotExist()

        return self._roles_channel

    @property
    def general_channel(self) -> TextChannel:
        if self._general_channel is None or discord.utils.get(self.css_guild.text_channels, id=self._general_channel.id) is None:
            raise GeneralChannelDoesNotExist()

        return self._general_channel


intents: Intents = Intents.default()
# noinspection PyDunderSlots,PyUnresolvedReferences
intents.members = True

bot = TeXBot(intents=intents)

cogs_list = {
    "events",
    "commands"
}
cog: str
for cog in cogs_list:
    bot.load_extension(f"cogs.{cog}")


if __name__ == "__main__":
    bot.run(settings["DISCORD_BOT_TOKEN"])
