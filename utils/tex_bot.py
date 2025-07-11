"""Custom Pycord Bot class implementation."""

import logging
import re
from typing import TYPE_CHECKING, override

import aiohttp
import discord
from discord import Webhook

from config import settings
from exceptions import (
    ApplicantRoleDoesNotExistError,
    ArchivistRoleDoesNotExistError,
    ChannelDoesNotExistError,
    CommitteeElectRoleDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    DiscordMemberNotInMainGuildError,
    EveryoneRoleCouldNotBeRetrievedError,
    GeneralChannelDoesNotExistError,
    GuestRoleDoesNotExistError,
    GuildDoesNotExistError,
    MemberRoleDoesNotExistError,
    RoleDoesNotExistError,
    RolesChannelDoesNotExistError,
    RulesChannelDoesNotExistError,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Sequence
    from logging import Logger
    from typing import Final, LiteralString, NoReturn

    from utils import AllChannelTypes

__all__: "Sequence[str]" = ("TeXBot",)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class TeXBot(discord.Bot):
    """
    Subclass of the default Bot class provided by Pycord.

    This subclass allows for storing commonly accessed roles and channels
    from your group's Discord guild, while also raising the correct errors
    if these objects do not exist.
    """

    @override
    def __init__(self, *args: object, **options: object) -> None:
        """Initialise a new Pycord Bot subclass with empty shortcut accessors."""
        self._main_guild: discord.Guild | None = None
        self._committee_role: discord.Role | None = None
        self._committee_elect_role: discord.Role | None = None
        self._guest_role: discord.Role | None = None
        self._member_role: discord.Role | None = None
        self._archivist_role: discord.Role | None = None
        self._applicant_role: discord.Role | None = None
        self._roles_channel: discord.TextChannel | None = None
        self._general_channel: discord.TextChannel | None = None
        self._rules_channel: discord.TextChannel | None = None
        self._exit_was_due_to_kill_command: bool = False

        self._main_guild_set: bool = False

        super().__init__(*args, **options)  # type: ignore[no-untyped-call]

    @override
    async def close(self) -> "NoReturn":  # type: ignore[misc]
        await super().close()

        logger.info("TeX-Bot manually terminated.")

    @property
    def EXIT_WAS_DUE_TO_KILL_COMMAND(self) -> bool:  # noqa: N802
        """Return whether the TeX-Bot exited due to the kill command being used."""
        return self._exit_was_due_to_kill_command

    @property
    def main_guild(self) -> discord.Guild:
        """
        Shortcut accessor to your group's Discord guild object.

        This shortcut accessor provides a consistent way of accessing
        your group's Discord guild object without having to repeatedly search for it,
        in the bot's list of guilds, by its ID.

        Raises `GuildDoesNotExist` if the given ID does not link to a valid Discord guild.
        """
        MAIN_GUILD_EXISTS: Final[bool] = bool(
            self._main_guild
            and self._check_guild_accessible(settings["_DISCORD_MAIN_GUILD_ID"])
        )
        if not MAIN_GUILD_EXISTS:
            raise GuildDoesNotExistError(guild_id=settings["_DISCORD_MAIN_GUILD_ID"])

        return self._main_guild  # type: ignore[return-value]

    @property
    async def committee_role(self) -> discord.Role:
        """
        Shortcut accessor to the committee role.

        The committee role is the role held by elected members
        of your community group's committee.
        Many commands are limited to use by only committee members.

        Raises `CommitteeRoleDoesNotExist` if the role does not exist.
        """
        if not self._committee_role or not self._main_guild_has_role(self._committee_role):
            self._committee_role = discord.utils.get(
                await self.main_guild.fetch_roles(), name="Committee"
            )

        if not self._committee_role:
            raise CommitteeRoleDoesNotExistError

        return self._committee_role

    @property
    async def committee_elect_role(self) -> discord.Role:
        """
        Shortcut accessor to the "Committee-Elect" role.

        The "Committee-Elect" role is the role held by committee members
        after they have been elected, but before the handover period has concluded.

        Raises `CommitteeElectRoleDoesNotExist` if the role does not exist.
        """
        COMMITTEE_ELECT_ROLE_NEEDS_FETCHING: Final[bool] = bool(
            not self._committee_elect_role
            or not self._main_guild_has_role(self._committee_elect_role)
        )
        if COMMITTEE_ELECT_ROLE_NEEDS_FETCHING:
            self._committee_elect_role = discord.utils.get(
                await self.main_guild.fetch_roles(), name="Committee-Elect"
            )

        if not self._committee_elect_role:
            raise CommitteeElectRoleDoesNotExistError

        return self._committee_elect_role

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
        if not self._guest_role or not self._main_guild_has_role(self._guest_role):
            self._guest_role = discord.utils.get(
                await self.main_guild.fetch_roles(), name="Guest"
            )

        if not self._guest_role:
            raise GuestRoleDoesNotExistError

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
        if not self._member_role or not self._main_guild_has_role(self._member_role):
            self._member_role = discord.utils.get(self.main_guild.roles, name="Member")
            self._member_role = discord.utils.get(
                await self.main_guild.fetch_roles(), name="Member"
            )

        if not self._member_role:
            raise MemberRoleDoesNotExistError

        return self._member_role

    @property
    async def archivist_role(self) -> discord.Role:
        """
        Shortcut accessor to the archivist role.

        The archivist role is the one that allows members to see channels and categories
        that are no longer in use, which are hidden from all other members.

        Raises `ArchivistRoleDoesNotExist` if the role does not exist.
        """
        if not self._archivist_role or not self._main_guild_has_role(self._archivist_role):
            self._archivist_role = discord.utils.get(
                await self.main_guild.fetch_roles(), name="Archivist"
            )

        if not self._archivist_role:
            raise ArchivistRoleDoesNotExistError

        return self._archivist_role

    @property
    async def applicant_role(self) -> discord.Role:
        """
        Shortcut accessor to the applicant role.

        The applicant role allows users to see the specific applicant channels.
        """
        if not self._applicant_role or not self._main_guild_has_role(self._applicant_role):
            self._applicant_role = discord.utils.get(
                await self.main_guild.fetch_roles(), name="Applicant"
            )

        if not self._applicant_role:
            raise ApplicantRoleDoesNotExistError

        return self._applicant_role

    @property
    async def roles_channel(self) -> discord.TextChannel:
        """
        Shortcut accessor to the welcome text channel.

        The roles text channel is the one that contains the message declaring all the
        available opt-in roles to members.

        Raises `RolesChannelDoesNotExist` if the channel does not exist.
        """
        if not self._roles_channel or not self._main_guild_has_channel(self._roles_channel):
            self._roles_channel = await self._fetch_main_guild_text_channel("roles")

        if not self._roles_channel:
            raise RolesChannelDoesNotExistError

        return self._roles_channel

    @property
    async def general_channel(self) -> discord.TextChannel:
        """
        Shortcut accessor to the general text channel.

        Raises `GeneralChannelDoesNotExist` if the channel does not exist.
        """
        if not self._general_channel or not self._main_guild_has_channel(
            self._general_channel
        ):
            self._general_channel = await self._fetch_main_guild_text_channel("general")

        if not self._general_channel:
            raise GeneralChannelDoesNotExistError

        return self._general_channel

    @property
    async def rules_channel(self) -> discord.TextChannel:
        """
        Shortcut accessor to the rules text channel.

        The rules text channel is the one that contains the welcome message and rules.

        Raises `RulesChannelDoesNotExist` if the channel does not exist.
        """
        if not self._rules_channel or not self._main_guild_has_channel(self._rules_channel):
            self._rules_channel = (
                self.main_guild.rules_channel
                or await self._fetch_main_guild_text_channel("welcome")
            )

        if not self._rules_channel:
            raise RulesChannelDoesNotExistError

        return self._rules_channel

    @property
    def group_full_name(self) -> str:
        """
        The full name of your community group.

        This is substituted into many error/welcome messages sent into your Discord guild,
        by TeX-Bot.
        The group-full-name is either retrieved from the provided environment variable
        or automatically identified from the name of your group's Discord guild.
        """
        return (
            settings["_GROUP_FULL_NAME"]
            if settings["_GROUP_FULL_NAME"]
            else (
                "The Computer Science Society"
                if (
                    "computer science society" in self.main_guild.name.lower()
                    or "css" in self.main_guild.name.lower()
                )
                else self.main_guild.name
            )
        )

    @property
    def group_short_name(self) -> str:
        """
        The short colloquial name of your community group.

        This defaults to `TeXBot.group_full_name`,
        if no group-short-name is provided/could not be determined.
        """
        return (
            (
                settings["_GROUP_SHORT_NAME"]
                if settings["_GROUP_SHORT_NAME"]
                else (
                    "CSS"
                    if (
                        "computer science society" in self.group_full_name.lower()
                        or "css" in self.group_full_name.lower()
                    )
                    else self.group_full_name
                )
            )
            .replace("the", "")
            .replace("THE", "")
            .replace("The", "")
            .strip()
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
                "computer science society" in self.group_full_name.lower()
                or "css" in self.group_full_name.lower()
                or "uob" in self.group_full_name.lower()
                or "university of birmingham" in self.group_full_name.lower()
                or "uob" in self.group_full_name.lower()
                or (
                    "bham" in self.group_full_name.lower()
                    and "uni" in self.group_full_name.lower()
                )
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
                "computer science society" in self.group_full_name.lower()
                or "css" in self.group_full_name.lower()
                or "uob" in self.group_full_name.lower()
                or "university of birmingham" in self.group_full_name.lower()
                or "uob" in self.group_full_name.lower()
                or (
                    "bham" in self.group_full_name.lower()
                    and "uni" in self.group_full_name.lower()
                )
            )
            else "our community moderators"
        )

    def _check_guild_accessible(self, guild_id: int) -> bool:
        return bool(discord.utils.get(self.guilds, id=guild_id))

    def _main_guild_has_role(self, role: discord.Role) -> bool:
        return bool(discord.utils.get(self.main_guild.roles, id=role.id))

    def _main_guild_has_channel(self, channel: discord.TextChannel) -> bool:
        return bool(discord.utils.get(self.main_guild.text_channels, id=channel.id))

    async def _fetch_main_guild_text_channel(
        self, name: "LiteralString"
    ) -> discord.TextChannel | None:
        text_channel: AllChannelTypes | None = discord.utils.get(
            await self.main_guild.fetch_channels(), name=name, type=discord.ChannelType.text
        )

        if text_channel is not None and not isinstance(text_channel, discord.TextChannel):
            INVALID_TEXT_CHANNEL_MESSAGE: Final[str] = (
                f"Received non text channel when attempting to fetch {name} text channel."
            )
            raise TypeError(INVALID_TEXT_CHANNEL_MESSAGE)

        return text_channel

    async def perform_kill_and_close(
        self, initiated_by_user: discord.User | discord.Member | None = None
    ) -> "NoReturn":
        """
        Shutdown TeX-Bot by using the "/kill" command.

        A log message will also be sent, announcing the user that requested the shutdown.
        """
        if self.EXIT_WAS_DUE_TO_KILL_COMMAND:
            EXIT_FLAG_ALREADY_SET_MESSAGE: Final[str] = (
                "The kill & close command has already been used. Invalid state."
            )
            raise RuntimeError(EXIT_FLAG_ALREADY_SET_MESSAGE)

        if initiated_by_user:
            logger.info("Manual shutdown initiated by %s.", initiated_by_user)

        self._exit_was_due_to_kill_command = True
        await self.close()

    async def get_everyone_role(self) -> discord.Role:
        """
        Util method to retrieve the "@everyone" role from your group's Discord guild.

        Raises `EveryoneRoleCouldNotBeRetrieved` if the @everyone role
        could not be retrieved.
        """
        everyone_role: discord.Role | None = discord.utils.get(
            self.main_guild.roles, name="@everyone"
        )
        if not everyone_role:
            raise EveryoneRoleCouldNotBeRetrievedError

        return everyone_role

    async def check_user_has_committee_role(self, user: discord.Member | discord.User) -> bool:
        """Util method to validate whether the given user has the "Committee" role."""
        return await self.committee_role in (await self.get_main_guild_member(user)).roles

    def set_main_guild(self, main_guild: discord.Guild) -> None:
        """
        Set the main_guild value that TeX-Bot will reference in the future.

        This can only be set once.
        """
        if self._main_guild_set:
            MAIN_GUILD_SET_MESSAGE: Final[str] = (
                "TeX-Bot's main_guild property has already been set, it cannot be changed."
            )
            raise RuntimeError(MAIN_GUILD_SET_MESSAGE)

        self._main_guild = main_guild
        self._main_guild_set = True

    async def get_main_guild_member(
        self, user: discord.Member | discord.User
    ) -> discord.Member:
        """
        Util method to retrieve a member of your group's Discord guild from their User object.

        Raises `DiscordMemberNotInMainGuild` if the user is not in your group's Discord guild.
        """
        main_guild_member: discord.Member | None = self.main_guild.get_member(user.id)
        if not main_guild_member:
            raise DiscordMemberNotInMainGuildError(user_id=user.id)

        return main_guild_member

    async def get_member_from_str_id(self, str_member_id: str) -> discord.Member:
        """
        Retrieve a member of your group's Discord guild by their ID.

        Raises `ValueError` if the provided ID does not represent any member
        of your group's Discord guild.
        """
        str_member_id = re.sub(r"\A\s*(<@)(.*)(?(1)>|)\s*\Z", r"\2", str_member_id)

        if not re.fullmatch(r"\A\d{17,20}\Z", str_member_id):
            INVALID_USER_ID_MESSAGE: Final[str] = f"'{str_member_id}' is not a valid user ID."
            raise ValueError(INVALID_USER_ID_MESSAGE)

        user: discord.User | None = self.get_user(int(str_member_id))
        if not user:
            raise ValueError(
                DiscordMemberNotInMainGuildError(user_id=int(str_member_id)).message
            )

        user_not_in_main_guild_error: DiscordMemberNotInMainGuildError
        try:
            member: discord.Member = await self.get_main_guild_member(user)
        except DiscordMemberNotInMainGuildError as user_not_in_main_guild_error:
            raise ValueError from user_not_in_main_guild_error

        return member

    async def fetch_log_channel(self) -> discord.TextChannel:
        """
        Retrieve the Discord log channel.

        If no DISCORD_LOG_CHANNEL_WEBHOOK_URL is specified,
        a ValueError exception will be raised.
        """
        if not settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]:
            NO_LOG_CHANNEL_MESSAGE: Final[str] = (
                "Cannot fetch log channel, "
                "when no DISCORD_LOG_CHANNEL_WEBHOOK_URL has been set."
            )
            raise ValueError(NO_LOG_CHANNEL_MESSAGE)

        session: aiohttp.ClientSession
        async with aiohttp.ClientSession() as session:
            partial_webhook: Webhook = Webhook.from_url(
                settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"], session=session
            )

            full_webhook: Webhook = await partial_webhook.fetch()
            if not full_webhook.channel:
                full_webhook = await self.fetch_webhook(partial_webhook.id)

            if not full_webhook.channel:
                LOG_CHANNEL_NOT_FOUND_MESSAGE: Final[str] = "Failed to fetch log channel."
                raise RuntimeError(LOG_CHANNEL_NOT_FOUND_MESSAGE)

            return full_webhook.channel

    @classmethod
    async def get_mention_string(
        cls,
        channel_coroutine: "Awaitable[discord.TextChannel | discord.Role]",
        default: str | None = None,
    ) -> str:
        """Return the mention string for a given role/channel, even if it does not exist."""
        try:
            return (await channel_coroutine).mention
        except RoleDoesNotExistError as e:
            return f"@{e.ROLE_NAME}" if default is None else default
        except ChannelDoesNotExistError as e:
            return f"**`#{e.CHANNEL_NAME}`**" if default is None else default
        except RulesChannelDoesNotExistError:
            return "**`#welcome`**" if default is None else default
