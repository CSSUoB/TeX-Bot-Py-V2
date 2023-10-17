"""Utility classes & functions provided for use across the whole of the project."""

import os
import re
import sys
from argparse import ArgumentParser, Namespace

import discord

# NOTE: Preventing loading modules that would cause errors if this file has been run from the command-line without pre-initialisation
if __name__ != "__main__":
    import io
    import math
    from typing import TYPE_CHECKING, Any, Final, TypeAlias

    import matplotlib.pyplot as plt
    import mplcyberpunk

    from config import settings
    from exceptions import (
        ArchivistRoleDoesNotExist,
        CommitteeRoleDoesNotExist,
        EveryoneRoleCouldNotBeRetrieved,
        GeneralChannelDoesNotExist,
        GuestRoleDoesNotExist,
        GuildDoesNotExist,
        MemberRoleDoesNotExist,
        RolesChannelDoesNotExist,
        RulesChannelDoesNotExist,
        UserNotInCSSDiscordServer,
    )

    if TYPE_CHECKING:
        from collections.abc import Collection

        from matplotlib.text import Text as Plot_Text

    ChannelTypes: TypeAlias = (
        discord.VoiceChannel
        | discord.StageChannel
        | discord.TextChannel
        | discord.ForumChannel
        | discord.CategoryChannel
        | None
    )


# noinspection PyShadowingNames
def generate_invite_url(discord_bot_application_id: str, discord_guild_id: int) -> str:
    """
    Generate the correct OAuth invite URL for the bot.

    This invite URL directs to the given Discord server and requests only the permissions
    required for the bot to run.
    """
    return discord.utils.oauth_url(
        client_id=discord_bot_application_id,
        permissions=discord.Permissions(
            manage_roles=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            read_message_history=True,
            mention_everyone=True,
            add_reactions=True,
            use_slash_commands=True,
            kick_members=True,
            manage_channels=True,
            view_audit_log=True
        ),
        guild=discord.Object(id=discord_guild_id),
        scopes=("bot", "applications.commands"),
        disable_guild_select=True
    )


# NOTE: Preventing using modules that have not been loaded if this file has been run from the command-line
if __name__ != "__main__":
    # noinspection SpellCheckingInspection
    def plot_bar_chart(data: dict[str, int], xlabel: str, ylabel: str, title: str, filename: str, description: str, extra_text: str = "") -> discord.File:  # noqa: E501
        """Generate an image of a plot bar chart from the given data & format variables."""
        plt.style.use("cyberpunk")

        max_data_value: int = max(data.values()) + 1

        # NOTE: The "extra_values" dictionary represents columns of data that should be formatted differently to the standard data columns
        extra_values: dict[str, int] = {}
        if "Total" in data:
            extra_values["Total"] = data.pop("Total")

        if len(data) > 4:
            data = {
                key: value
                for index, (key, value) in enumerate(data.items())
                if value > 0 or index <= 4
            }

        bars = plt.bar(*zip(*data.items(), strict=True))

        if extra_values:
            extra_bars = plt.bar(*zip(*extra_values.items(), strict=True))
            mplcyberpunk.add_bar_gradient(extra_bars)

        mplcyberpunk.add_bar_gradient(bars)

        xticklabels: Collection[Plot_Text] = plt.gca().get_xticklabels()
        count_xticklabels: int = len(xticklabels)

        index: int
        tick_label: Plot_Text
        for index, tick_label in enumerate(xticklabels):
            if tick_label.get_text() == "Total":
                tick_label.set_fontweight("bold")

            # NOTE: Shifts the y location of every other horizontal label down so that they do not overlap with one-another
            if index % 2 == 1 and count_xticklabels > 4:
                tick_label.set_y(tick_label.get_position()[1] - 0.044)

        plt.yticks(range(0, max_data_value, math.ceil(max_data_value / 15)))

        xlabel_obj: Plot_Text = plt.xlabel(
            xlabel,
            fontweight="bold",
            fontsize="large",
            wrap=True
        )
        xlabel_obj._get_wrap_line_width = lambda: 475  # type: ignore[attr-defined] # noqa: SLF001

        ylabel_obj: Plot_Text = plt.ylabel(
            ylabel,
            fontweight="bold",
            fontsize="large",
            wrap=True
        )
        ylabel_obj._get_wrap_line_width = lambda: 375  # type: ignore[attr-defined] # noqa: SLF001

        title_obj: Plot_Text = plt.title(title, fontsize="x-large", wrap=True)
        title_obj._get_wrap_line_width = lambda: 500  # type: ignore[attr-defined] # noqa: SLF001

        if extra_text:
            extra_text_obj: Plot_Text = plt.text(
                0.5,
                -0.27,
                extra_text,
                ha="center",
                transform=plt.gca().transAxes,
                wrap=True,
                fontstyle="italic",
                fontsize="small"
            )
            extra_text_obj._get_wrap_line_width = lambda: 400  # type: ignore[attr-defined] # noqa: SLF001
            plt.subplots_adjust(bottom=0.2)

        plot_file = io.BytesIO()
        plt.savefig(plot_file, format="png")
        plt.close()
        plot_file.seek(0)

        discord_plot_file: discord.File = discord.File(
            plot_file,
            filename,
            description=description
        )

        plot_file.close()

        return discord_plot_file


    def amount_of_time_formatter(value: float, time_scale: str) -> str:
        """
        Format the amount of time value according to the provided time_scale.

        E.g. past "1 days" => past "day",
        past "2.00 weeks" => past "2 weeks",
        past "3.14159 months" => past "3.14 months"
        """
        if value == 1 or float(f"{value:.2f}") == 1:
            return f"{time_scale}"

        if value % 1 == 0 or float(f"{value:.2f}") % 1 == 0:
            return f"{int(value)} {time_scale}s"

        return f"{value:.2f} {time_scale}s"


    class TeXBot(discord.Bot):
        """
        Subclass of the default Bot class provided by Pycord.

        This subclass allows for storing commonly accessed roles & channels from the
        CSS Discord Server, while also raising the correct errors if these objects do not
        exist.
        """

        def __init__(self, *args: Any, **options: Any) -> None:
            """Initialize a new discord.Bot subclass with empty shortcut accessors."""
            self._css_guild: discord.Guild | None = None
            self._committee_role: discord.Role | None = None
            self._guest_role: discord.Role | None = None
            self._member_role: discord.Role | None = None
            self._archivist_role: discord.Role | None = None
            self._applicant_role: discord.Role | None = None
            self._roles_channel: discord.TextChannel | None = None
            self._general_channel: discord.TextChannel | None = None
            self._rules_channel: discord.TextChannel | None = None

            self._css_guild_set: bool = False

            super().__init__(*args, **options)  # type: ignore[no-untyped-call]

        @property
        def css_guild(self) -> discord.Guild:
            """
            Shortcut accessor to the CSS guild (Discord server).

            This shortcut accessor provides a consistent way of accessing the CSS server object
            without having to repeatedly search for it, in the bot's list of guilds, by its ID.
            """
            if not self._css_guild or not self._bot_has_guild(settings["DISCORD_GUILD_ID"]):
                raise GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"])

            return self._css_guild

        @property
        async def committee_role(self) -> discord.Role:
            """
            Shortcut accessor to the committee role.

            The committee role is the role held by elected members of the CSS committee.
            Many commands are limited to use by only committee members.
            """
            if not self._committee_role or not self._guild_has_role(self._committee_role):
                self._committee_role = discord.utils.get(
                    await self.css_guild.fetch_roles(),
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
            main channels of the CSS Discord server.
            It is given to members only after they have sent a message with a short
            introduction about themselves.
            """
            if not self._guest_role or not self._guild_has_role(self._guest_role):
                self._guest_role = discord.utils.get(
                    await self.css_guild.fetch_roles(),
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
            verified a purchased membership to CSS.
            It provides bragging rights to other server members by showing the member's name in
            green!
            """
            if not self._member_role or not self._guild_has_role(self._member_role):
                self._member_role = discord.utils.get(self.css_guild.roles, name="Member")
                self._member_role = discord.utils.get(
                    await self.css_guild.fetch_roles(),
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
            """
            if not self._archivist_role or not self._guild_has_role(self._archivist_role):
                self._archivist_role = discord.utils.get(
                    await self.css_guild.fetch_roles(),
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
            """
            if not self._roles_channel or not self._guild_has_channel(self._roles_channel):
                self._roles_channel = await self._fetch_text_channel("roles")

            if not self._roles_channel:
                raise RolesChannelDoesNotExist

            return self._roles_channel

        @property
        async def general_channel(self) -> discord.TextChannel:
            """Shortcut accessor to the general text channel."""
            if not self._general_channel or not self._guild_has_channel(self._general_channel):
                self._general_channel = await self._fetch_text_channel("general")

            if not self._general_channel:
                raise GeneralChannelDoesNotExist

            return self._general_channel

        @property
        async def rules_channel(self) -> discord.TextChannel:
            """
            Shortcut accessor to the welcome text channel.

            The welcome text channel is the one that contains the welcome message & rules.
            """
            if not self._rules_channel or not self._guild_has_channel(self._rules_channel):
                self._rules_channel = (
                    self.css_guild.rules_channel
                    or await self._fetch_text_channel("welcome")
                )

            if not self._rules_channel:
                raise RulesChannelDoesNotExist

            return self._rules_channel

        def _bot_has_guild(self, guild_id: int) -> bool:
            return bool(discord.utils.get(self.guilds, id=guild_id))

        def _guild_has_role(self, role: discord.Role) -> bool:
            return bool(discord.utils.get(self.css_guild.roles, id=role.id))

        def _guild_has_channel(self, channel: discord.TextChannel) -> bool:
            return bool(discord.utils.get(self.css_guild.text_channels, id=channel.id))

        async def _fetch_text_channel(self, name: str) -> discord.TextChannel | None:
            text_channel: ChannelTypes = discord.utils.get(
                await self.css_guild.fetch_channels(),
                name=name,
                type=discord.ChannelType.text
            )

            if text_channel is not None and not isinstance(text_channel, discord.TextChannel):
                INVALID_TEXT_CHANNEL_MESSAGE: Final[str] = (
                    f"Received non text channel when attempting to fetch {name} text channel."
                )
                raise TypeError(INVALID_TEXT_CHANNEL_MESSAGE)

            return text_channel

        async def get_css_user(self, user: discord.Member | discord.User) -> discord.Member:
            """Util method to retrieve a member of the CSS Discord server by their ID."""
            css_user: discord.Member | None = self.css_guild.get_member(user.id)
            if not css_user:
                raise UserNotInCSSDiscordServer(user_id=user.id)
            return css_user

        async def get_everyone_role(self) -> discord.Role:
            """Util method to retrieve the "@everyone" role from the CSS Discord server."""
            everyone_role: discord.Role | None = discord.utils.get(
                self.css_guild.roles,
                name="@everyone"
            )
            if not everyone_role:
                raise EveryoneRoleCouldNotBeRetrieved
            return everyone_role

        async def check_user_has_committee_role(self, user: discord.Member | discord.User) -> bool:  # noqa: E501
            """Util method to validate whether the given user has the "Committee" role."""
            return await self.committee_role in (await self.get_css_user(user)).roles

        def set_css_guild(self, css_guild: discord.Guild) -> None:
            """
            Set the css_guild value that the bot will reference in the future.

            This can only be set once.
            """
            if self._css_guild_set:
                CSS_GUILD_SET_MESSAGE: Final[str] = (
                    "The bot's css_guild property has already been set, it cannot be changed."
                )
                raise RuntimeError(CSS_GUILD_SET_MESSAGE)

            self._css_guild = css_guild
            self._css_guild_set = True


if __name__ == "__main__":
    arg_parser: ArgumentParser = ArgumentParser(
        description="Executes common command-line utility functions"
    )
    function_subparsers = arg_parser.add_subparsers(
        title="functions",
        required=True,
        help="Utility function to execute",
        dest="function"
    )

    generate_invite_url_arg_parser: ArgumentParser = function_subparsers.add_parser(
        "generate_invite_url",
        description="Generates the URL to invite the bot to the given Discord server"
    )
    generate_invite_url_arg_parser.add_argument(
        "discord_bot_application_id",
        help="Must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)"
    )
    generate_invite_url_arg_parser.add_argument(
        "discord_guild_id",
        nargs="?",
        help="The value of the environment variable DISCORD_GUILD_ID is used"
             " if this argument is omitted. Must be a valid Discord guild ID"
             " (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
    )

    parsed_args: Namespace = arg_parser.parse_args()

    if parsed_args.function == "generate_invite_url":
        if not re.match(r"\A\d{17,20}\Z", parsed_args.discord_bot_application_id):
            generate_invite_url_arg_parser.error(
                "discord_bot_application_id must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)"
            )

        discord_guild_id: str = parsed_args.discord_guild_id or ""
        if not discord_guild_id:
            import dotenv

            dotenv.load_dotenv()
            discord_guild_id = os.getenv("DISCORD_GUILD_ID", "")

            if not discord_guild_id:
                generate_invite_url_arg_parser.error(
                    "discord_guild_id must be provided as an argument"
                    " to the generate_invite_url utility function"
                    " or otherwise set the DISCORD_GUILD_ID environment variable"
                )

        if not re.match(r"\A\d{17,20}\Z", discord_guild_id):
            generate_invite_url_arg_parser.error(
                "discord_guild_id must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
            )

        sys.stdout.write(
            generate_invite_url(
                parsed_args.discord_bot_application_id,
                int(discord_guild_id)
            )
        )
        sys.stdout.flush()

        generate_invite_url_arg_parser.exit(status=0)
