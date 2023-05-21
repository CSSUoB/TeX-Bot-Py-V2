import io
import math
from typing import Collection

import discord
import matplotlib.pyplot as plt  # type: ignore
import mplcyberpunk  # type: ignore
from matplotlib.text import Text as Plot_Text  # type: ignore

from exceptions import GuildDoesNotExist
from setup import settings


def get_oauth_url() -> str:
    return discord.utils.oauth_url(
        client_id=settings["DISCORD_BOT_APPLICATION_ID"],
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
            manage_channels=True
        ),
        guild=discord.Object(id=settings["DISCORD_GUILD_ID"]),
        scopes={"bot", "applications.commands"},
        disable_guild_select=True
    )


# noinspection SpellCheckingInspection
def plot_bar_chart(data: dict[str, int], xlabel: str, ylabel: str, title: str, filename: str, description: str, extra_text: str = "") -> discord.File:
    plt.style.use("cyberpunk")

    max_data_value: int = max(data.values()) + 1

    extra_values: dict[str, int] = {}
    if "Total" in data:
        extra_values["Total"] = data.pop("Total")

    bars = plt.bar(data.keys(), data.values())

    if extra_values:
        extra_bars = plt.bar(extra_values.keys(), extra_values.values())
        mplcyberpunk.add_bar_gradient(extra_bars)

    mplcyberpunk.add_bar_gradient(bars)

    xticklabels: Collection[Plot_Text] = plt.gca().get_xticklabels()
    count_xticklabels: int = len(xticklabels)

    index: int
    tick_label: Plot_Text
    for index, tick_label in enumerate(xticklabels):
        if tick_label.get_text() == "Total":
            tick_label.set_fontweight("bold")

        if index % 2 == 1 and count_xticklabels > 4:
            tick_label.set_y(tick_label.get_position()[1] - 0.044)

    plt.yticks(range(0, max_data_value, math.ceil(max_data_value / 15)))

    xlabel_obj: Plot_Text = plt.xlabel(xlabel, fontweight="bold", fontsize="large", wrap=True)
    xlabel_obj._get_wrap_line_width = lambda: 475

    ylabel_obj: Plot_Text = plt.ylabel(ylabel, fontweight="bold", fontsize="large", wrap=True)
    ylabel_obj._get_wrap_line_width = lambda: 375

    title_obj: Plot_Text = plt.title(title, fontsize="x-large", wrap=True)
    title_obj._get_wrap_line_width = lambda: 500

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
        extra_text_obj._get_wrap_line_width = lambda: 400
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


def time_formatter(value: float, scale: str) -> str:
    if value == 1:
        return f"{scale}"

    elif value % 1 == 0:
        return f"{value} {scale}s"

    else:
        return f"{value:.3} {scale}s"


class TeXBot(discord.Bot):
    def __init__(self, *args, **kwargs) -> None:
        self._css_guild: discord.Guild | None = None
        self._committee_role: discord.Role | None = None
        self._guest_role: discord.Role | None = None
        self._member_role: discord.Role | None = None
        self._archivist_role: discord.Role | None = None
        self._roles_channel: discord.TextChannel | None = None
        self._general_channel: discord.TextChannel | None = None
        self._welcome_channel: discord.TextChannel | None = None

        super().__init__(*args, **kwargs)

    @property
    def css_guild(self) -> discord.Guild:
        if not self._css_guild or not discord.utils.get(self.guilds, id=settings["DISCORD_GUILD_ID"]):
            raise GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"])

        return self._css_guild

    @property
    def committee_role(self) -> discord.Role | None:
        if not self._committee_role or not discord.utils.get(self.css_guild.roles, id=self._committee_role.id):
            self._committee_role = discord.utils.get(self.css_guild.roles, name="Committee")

        return self._committee_role

    @property
    def guest_role(self) -> discord.Role | None:
        if not self._guest_role or not discord.utils.get(self.css_guild.roles, id=self._guest_role.id):
            self._guest_role = discord.utils.get(self.css_guild.roles, name="Guest")

        return self._guest_role

    @property
    def member_role(self) -> discord.Role | None:
        if not self._member_role or not discord.utils.get(self.css_guild.roles, id=self._member_role.id):
            self._member_role = discord.utils.get(self.css_guild.roles, name="Member")

        return self._member_role

    @property
    def archivist_role(self) -> discord.Role | None:
        if not self._archivist_role or not discord.utils.get(self.css_guild.roles, id=self._archivist_role.id):
            self._archivist_role = discord.utils.get(self.css_guild.roles, name="Archivist")

        return self._archivist_role

    @property
    def roles_channel(self) -> discord.TextChannel | None:
        if not self._roles_channel or not discord.utils.get(self.css_guild.text_channels, id=self._roles_channel.id):
            self._roles_channel = discord.utils.get(self.css_guild.text_channels, name="roles")

        return self._roles_channel

    @property
    def general_channel(self) -> discord.TextChannel | None:
        if not self._general_channel or not discord.utils.get(self.css_guild.text_channels, id=self._general_channel.id):
            self._general_channel = discord.utils.get(self.css_guild.text_channels, name="general")

        return self._general_channel

    @property
    def welcome_channel(self) -> discord.TextChannel | None:
        if not self._welcome_channel or not discord.utils.get(self.css_guild.text_channels, id=self._welcome_channel.id):
            self._welcome_channel = self.css_guild.rules_channel or discord.utils.get(self.css_guild.text_channels, name="welcome")

        return self._welcome_channel
