"""Custom bot implementation to override the default bot class provided by Pycord."""

from collections.abc import Sequence

__all__: Sequence[str] = ("TeXBot",)

import re
from typing import Any, Final, TypeAlias

import discord

from config import settings
from exceptions import (
    ArchivistRoleDoesNotExist,
    CommitteeRoleDoesNotExist,
    DiscordMemberNotInMainGuild,
    EveryoneRoleCouldNotBeRetrieved,
    GeneralChannelDoesNotExist,
    GuestRoleDoesNotExist,
    GuildDoesNotExist,
    MemberRoleDoesNotExist,
    RolesChannelDoesNotExist,
    RulesChannelDoesNotExist,
)

ChannelTypes: TypeAlias = (
    discord.VoiceChannel
    | discord.StageChannel
    | discord.TextChannel
    | discord.ForumChannel
    | discord.CategoryChannel
    | None
)


class TeXBot(discord.Bot):
    """
    Subclass of the default Bot class provided by Pycord.

    This subclass allows for storing commonly accessed roles & channels
    from your group's Discord guild, while also raising the correct errors
    if these objects do not exist.
    """

    def __init__(self, *args: Any, **options: Any) -> None:
        """Initialize a new discord.Bot subclass with empty shortcut accessors."""
        self._main_guild: discord.Guild | None = None
        self._committee_role: discord.Role | None = None
        self._guest_role: discord.Role | None = None
        self._member_role: discord.Role | None = None
        self._archivist_role: discord.Role | None = None
        self._applicant_role: discord.Role | None = None
        self._roles_channel: discord.TextChannel | None = None
        self._general_channel: discord.TextChannel | None = None
        self._rules_channel: discord.TextChannel | None = None

        self._main_guild_set: bool = False

        super().__init__(*args, **options)  # type: ignore[no-untyped-call]

    @property
    def main_guild(self) -> discord.Guild:
        """
        Shortcut accessor to your group's Discord guild object.

        This shortcut accessor provides a consistent way of accessing
        your group's Discord guild object without having to repeatedly search for it,
        in the bot's list of guilds, by its ID.

        Raises `GuildDoesNotExist` if the given ID does not link to a valid Discord guild.
        """
        if not self._main_guild or not self._bot_has_guild(settings["DISCORD_GUILD_ID"]):
            raise GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"])

        return self._main_guild

    @property
    async def committee_role(self) -> discord.Role:
        """
        Shortcut accessor to the committee role.

        The committee role is the role held by elected members
        of your community group's committee.
        Many commands are limited to use by only committee members.

        Raises `CommitteeRoleDoesNotExist` if the role does not exist.
        """
        if not self._committee_role or not self._guild_has_role(self._committee_role):
            self._committee_role = discord.utils.get(
                await self.main_guild.fetch_roles(),
                name="Committee"
            )

        if not self._committee_role:
            raise CommitteeRoleDoesNotExist

        return self._committee_role

    @property
    async def guest_role(self) -> discord.Role:
        """
        Shortcut accessor to the guest role.

        The guest role is the core role that provides members with access to talk in the
        main channels of your group's Discord guild.
        It is given to members only after they have sent a message with a short
        introduction about themselves.

        Raises `GuestRoleDoesNotExist` if the role does not exist.
        """
        if not self._guest_role or not self._guild_has_role(self._guest_role):
            self._guest_role = discord.utils.get(
                await self.main_guild.fetch_roles(),
                name="Guest"
            )

        if not self._guest_role:
            raise GuestRoleDoesNotExist

        return self._guest_role

    @property
    async def member_role(self) -> discord.Role:
        """
        Shortcut accessor to the member role.

        The member role is the one only accessible to server members after they have
        verified a purchased membership to your community group.
        It provides bragging rights to other server members by showing the member's name in
        green!

        Raises `MemberRoleDoesNotExist` if the role does not exist.
        """
        if not self._member_role or not self._guild_has_role(self._member_role):
            self._member_role = discord.utils.get(self.main_guild.roles, name="Member")
            self._member_role = discord.utils.get(
                await self.main_guild.fetch_roles(),
                name="Member"
            )

        if not self._member_role:
            raise MemberRoleDoesNotExist

        return self._member_role

    @property
    async def archivist_role(self) -> discord.Role:
        """
        Shortcut accessor to the archivist role.

        The archivist role is the one that allows members to see channels & categories
        that are no longer in use, which are hidden to all other members.

        Raises `ArchivistRoleDoesNotExist` if the role does not exist.
        """
        if not self._archivist_role or not self._guild_has_role(self._archivist_role):
            self._archivist_role = discord.utils.get(
                await self.main_guild.fetch_roles(),
                name="Archivist"
            )

        if not self._archivist_role:
            raise ArchivistRoleDoesNotExist

        return self._archivist_role

    @property
    async def roles_channel(self) -> discord.TextChannel:
        """
        Shortcut accessor to the welcome text channel.

        The roles text channel is the one that contains the message declaring all the
        available opt-in roles to members.

        Raises `RolesChannelDoesNotExist` if the channel does not exist.
        """
        if not self._roles_channel or not self._guild_has_channel(self._roles_channel):
            self._roles_channel = await self._fetch_text_channel("roles")

        if not self._roles_channel:
            raise RolesChannelDoesNotExist

        return self._roles_channel

    @property
    async def general_channel(self) -> discord.TextChannel:
        """
        Shortcut accessor to the general text channel.

        Raises `GeneralChannelDoesNotExist` if the channel does not exist.
        """
        if not self._general_channel or not self._guild_has_channel(self._general_channel):
            self._general_channel = await self._fetch_text_channel("general")

        if not self._general_channel:
            raise GeneralChannelDoesNotExist

        return self._general_channel

    @property
    async def rules_channel(self) -> discord.TextChannel:
        """
        Shortcut accessor to the rules text channel.

        The rules text channel is the one that contains the welcome message & rules.

        Raises `RulesChannelDoesNotExist` if the channel does not exist.
        """
        if not self._rules_channel or not self._guild_has_channel(self._rules_channel):
            self._rules_channel = (
                    self.main_guild.rules_channel
                    or await self._fetch_text_channel("welcome")
            )

        if not self._rules_channel:
            raise RulesChannelDoesNotExist

        return self._rules_channel

    @property
    def group_name(self) -> str:
        """
        The name of your community group.

        This is substituted into many error/welcome messages sent into your Discord guild,
        by the bot.
        The group name is either retrieved from the provided environment variable,
        or automatically identified from the name of your group's Discord guild.
        """
        group_name: Final[str | None] = settings["_GROUP_NAME"]
        return (
            group_name
            if group_name
            else (
                "CSS"
                if self.main_guild.name.lower() == "computer science society"
                else self.main_guild.name
            )
        )

    @property
    def group_full_name(self) -> str:
        """The full capitalised name of your community group."""
        return (
            "The Computer Science Society"
            if self.group_name.lower() in ("css", "computer science society")
            else self.group_name
        )

    @property
    def group_member_id_type(self) -> str:
        """
        The type of IDs that users input to become members.

        This ID type that is retrieved from your members-list.
        """
        return (
            "UoB Student"
            if (
                self.group_name.lower() in ("css", "computer science society")
                or "uob" in self.group_name.lower()
                or "birmingham" in self.group_name.lower()
            )
            else "community group"
        )

    @property
    def group_moderation_contact(self) -> str:
        """
        The name of the moderation group that Discord member bans will be reported to.

        This is used in the ban message sent to the user that committed the violation.
        """
        return (
            "the Guild of Students"
            if (
                self.group_name.lower() in ("css", "computer science society")
                or "uob" in self.group_name.lower()
                or "birmingham" in self.group_name.lower()
            )
            else "our community moderators"
        )

    def _bot_has_guild(self, guild_id: int) -> bool:
        return bool(discord.utils.get(self.guilds, id=guild_id))

    def _guild_has_role(self, role: discord.Role) -> bool:
        return bool(discord.utils.get(self.main_guild.roles, id=role.id))

    def _guild_has_channel(self, channel: discord.TextChannel) -> bool:
        return bool(discord.utils.get(self.main_guild.text_channels, id=channel.id))

    async def _fetch_text_channel(self, name: str) -> discord.TextChannel | None:
        text_channel: ChannelTypes = discord.utils.get(
            await self.main_guild.fetch_channels(),
            name=name,
            type=discord.ChannelType.text
        )

        if text_channel is not None and not isinstance(text_channel, discord.TextChannel):
            INVALID_TEXT_CHANNEL_MESSAGE: Final[str] = (
                f"Received non text channel when attempting to fetch {name} text channel."
            )
            raise TypeError(INVALID_TEXT_CHANNEL_MESSAGE)

        return text_channel

    async def get_everyone_role(self) -> discord.Role:
        """
        Util method to retrieve the "@everyone" role from your group's Discord guild.

        Raises `EveryoneRoleCouldNotBeRetrieved` if the @everyone role
        could not be retrieved.
        """
        everyone_role: discord.Role | None = discord.utils.get(
            self.main_guild.roles,
            name="@everyone"
        )
        if not everyone_role:
            raise EveryoneRoleCouldNotBeRetrieved
        return everyone_role

    async def check_user_has_committee_role(self, user: discord.Member | discord.User) -> bool:
        """Util method to validate whether the given user has the "Committee" role."""
        return await self.committee_role in (await self.get_main_guild_member(user)).roles

    def set_main_guild(self, main_guild: discord.Guild) -> None:
        """
        Set the main_guild value that the bot will reference in the future.

        This can only be set once.
        """
        if self._main_guild_set:
            MAIN_GUILD_SET_MESSAGE: Final[str] = (
                "The bot's main_guild property has already been set, it cannot be changed."
            )
            raise RuntimeError(MAIN_GUILD_SET_MESSAGE)

        self._main_guild = main_guild
        self._main_guild_set = True

    async def get_main_guild_member(self, user: discord.Member | discord.User) -> discord.Member:  # noqa: E501
        """
        Util method to retrieve a member of your group's Discord guild from their User object.

        Raises `DiscordMemberNotInMainGuild` if the user is not in your group's Discord guild.
        """
        main_guild_member: discord.Member | None = self.main_guild.get_member(user.id)
        if not main_guild_member:
            raise DiscordMemberNotInMainGuild(user_id=user.id)
        return main_guild_member

    async def get_member_from_str_id(self, str_member_id: str) -> discord.Member:
        """
        Retrieve a member of your group's Discord guild by their ID.

        Raises `ValueError` if the provided ID does not represent any member
        of your group's Discord guild.
        """
        str_member_id = str_member_id.replace("<@", "").replace(">", "")

        if not re.match(r"\A\d{17,20}\Z", str_member_id):
            INVALID_USER_ID_MESSAGE: Final[str] = (
                f"\"{str_member_id}\" is not a valid user ID."
            )
            raise ValueError(INVALID_USER_ID_MESSAGE)

        user: discord.User | None = self.get_user(int(str_member_id))
        if not user:
            raise ValueError(DiscordMemberNotInMainGuild(user_id=int(str_member_id)).message)
        try:
            member: discord.Member = await self.get_main_guild_member(user)
        except DiscordMemberNotInMainGuild as e:
            raise ValueError from e

        return member
