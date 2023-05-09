import discord
from discord import Guild, Object, Permissions, Role, TextChannel

from exceptions import GuildDoesNotExist
from setup import settings


def get_oauth_url():
    return discord.utils.oauth_url(
        client_id=settings["DISCORD_BOT_APPLICATION_ID"],
        permissions=Permissions(
            manage_roles=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            read_message_history=True,
            mention_everyone=True,
            add_reactions=True,
            use_slash_commands=True
        ),
        guild=Object(id=settings["DISCORD_GUILD_ID"]),
        scopes={"bot", "applications.commands"},
        disable_guild_select=True
    )


class TeXBot(discord.Bot):
    def __init__(self, *args, **kwargs):
        self._css_guild: Guild | None = None
        self._committee_role: Role | None = None
        self._guest_role: Role | None = None
        self._member_role: Role | None = None
        self._roles_channel: TextChannel | None = None
        self._general_channel: TextChannel | None = None

        super().__init__(*args, **kwargs)

    @property
    def css_guild(self) -> Guild:
        if self._css_guild is None or discord.utils.get(self.guilds, id=settings["DISCORD_GUILD_ID"]) is None:
            raise GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"])

        return self._css_guild

    @property
    def committee_role(self) -> Role | None:
        if self._committee_role is None or discord.utils.get(self.css_guild.roles, id=self._committee_role.id) is None:
            self._committee_role = discord.utils.get(self.css_guild.roles, name="Committee")

        return self._committee_role

    @property
    def guest_role(self) -> Role | None:
        if self._guest_role is None or discord.utils.get(self.css_guild.roles, id=self._guest_role.id) is None:
            self._guest_role = discord.utils.get(self.css_guild.roles, name="Guest")

        return self._guest_role

    @property
    def member_role(self) -> Role | None:
        if self._member_role is None or discord.utils.get(self.css_guild.roles, id=self._member_role.id) is None:
            self._member_role = discord.utils.get(self.css_guild.roles, name="Member")

        return self._member_role

    @property
    def roles_channel(self) -> TextChannel | None:
        if self._roles_channel is None or discord.utils.get(self.css_guild.text_channels, id=self._roles_channel.id) is None:
            self._roles_channel = discord.utils.get(self.css_guild.text_channels, name="roles")

        return self._roles_channel

    @property
    def general_channel(self) -> TextChannel | None:
        if self._general_channel is None or discord.utils.get(self.css_guild.text_channels, id=self._general_channel.id) is None:
            self._general_channel = discord.utils.get(self.css_guild.text_channels, name="general")

        return self._general_channel
