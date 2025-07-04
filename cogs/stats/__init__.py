"""Contains cog classes for any stats interactions."""

import math
import re
from typing import TYPE_CHECKING

import discord

from config import settings
from db.core.models import LeftDiscordMember
from utils import CommandChecks, TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

from .counts import get_channel_message_counts, get_server_message_counts
from .graphs import amount_of_time_formatter, plot_bar_chart

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Mapping, Sequence
    from typing import Final

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("StatsCommandsCog",)


class StatsCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/stats" command group and its command call-back methods."""

    _DISCORD_SERVER_NAME: "Final[str]" = f"""{
        "the "
        if (
            settings["_GROUP_SHORT_NAME"] is not None
            and (settings["_GROUP_SHORT_NAME"])
            .replace("the", "")
            .replace("THE", "")
            .replace("The", "")
            .strip()
        )
        else ""
    }{
        (
            (settings["_GROUP_SHORT_NAME"])
            .replace("the", "")
            .replace("THE", "")
            .replace("The", "")
            .strip()
        )
        if (
            settings["_GROUP_SHORT_NAME"] is not None
            and (settings["_GROUP_SHORT_NAME"])
            .replace("the", "")
            .replace("THE", "")
            .replace("The", "")
            .strip()
        )
        else "our community group's"
    }"""

    stats: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="stats",
        description=f"Various statistics about {_DISCORD_SERVER_NAME} Discord server",
    )

    @stats.command(
        name="channel", description="Displays the stats for the current/a given channel."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="channel",
        description="The channel to display the stats for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(
            TeXBotBaseCog.autocomplete_get_text_channels,  # type: ignore[arg-type]
        ),
        required=False,
        parameter_name="str_channel_id",
    )
    async def channel_stats(
        self, ctx: "TeXBotApplicationContext", str_channel_id: str
    ) -> None:
        """
        Definition & callback response of the "channel_stats" command.

        The "channel_stats" command sends a graph of the stats about messages sent in the given
        channel.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild

        channel_id: int = ctx.channel_id

        if str_channel_id:
            if not re.fullmatch(r"\A\d{17,20}\Z", str_channel_id):
                await self.command_send_error(
                    ctx, message=f"{str_channel_id!r} is not a valid channel ID."
                )
                return

            channel_id = int(str_channel_id)

        channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels, id=channel_id
        )
        if not channel:
            await self.command_send_error(
                ctx, message=f"Text channel with ID {str(channel_id)!r} does not exist."
            )
            return

        await ctx.defer(ephemeral=True)

        message_counts: Mapping[str, int] = await get_channel_message_counts(channel=channel)

        if math.ceil(max(message_counts.values()) / 15) < 1:
            await self.command_send_error(
                ctx=ctx, message="There are not enough messages sent in this channel."
            )
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            file=plot_bar_chart(
                message_counts,
                x_label="Role Name",
                y_label=(
                    f"""Number of Messages Sent (in the past {
                        amount_of_time_formatter(settings["STATISTICS_DAYS"].days, "day")
                    })"""
                ),
                title=f"Most Active Roles in #{channel.name}",
                filename=f"{channel.name}_channel_stats.png",
                description=(
                    "Bar chart of the number of messages "
                    f"sent by different roles in {channel.mention}."
                ),
                extra_text=(
                    "Messages sent by members with multiple roles are counted once "
                    "for each role "
                    "(except for @Member vs @Guest & @Committee vs @Committee-Elect)"
                ),
            ),
        )

    @stats.command(
        name="server",
        description=f"Displays the stats for the whole of {_DISCORD_SERVER_NAME}",
    )
    async def server_stats(self, ctx: "TeXBotApplicationContext") -> None:
        """
        Definition & callback response of the "server_stats" command.

        The "server_stats" command sends a graph of the stats about messages sent in the whole
        of your group's Discord guild.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        guest_role: discord.Role = await self.bot.guest_role

        await ctx.defer(ephemeral=True)

        message_counts: Mapping[str, Mapping[str, int]] = await get_server_message_counts(
            guild=main_guild, guest_role=guest_role
        )

        TOO_FEW_ROLES_STATS: Final[bool] = (
            math.ceil(max(message_counts["roles"].values()) / 15) < 1
        )
        TOO_FEW_CHANNELS_STATS: Final[bool] = (
            math.ceil(max(message_counts["channels"].values()) / 15) < 1
        )
        if TOO_FEW_ROLES_STATS or TOO_FEW_CHANNELS_STATS:
            await self.command_send_error(ctx, message="There are not enough messages sent.")
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            files=[
                plot_bar_chart(
                    message_counts["roles"],
                    x_label="Role Name",
                    y_label=(
                        f"""Number of Messages Sent (in the past {
                            amount_of_time_formatter(settings["STATISTICS_DAYS"].days, "day")
                        })"""
                    ),
                    title=(
                        f"Most Active Roles in the {self.bot.group_short_name} Discord Server"
                    ),
                    filename="roles_server_stats.png",
                    description=(
                        "Bar chart of the number of messages sent by different roles "
                        f"in the {self.bot.group_short_name} Discord server."
                    ),
                    extra_text=(
                        "Messages sent by members with multiple roles are counted once "
                        "for each role "
                        "(except for @Member vs @Guest & @Committee vs @Committee-Elect)"
                    ),
                ),
                plot_bar_chart(
                    message_counts["channels"],
                    x_label="Channel Name",
                    y_label=(
                        f"""Number of Messages Sent (in the past {
                            amount_of_time_formatter(settings["STATISTICS_DAYS"].days, "day")
                        })"""
                    ),
                    title=(
                        "Most Active Channels "
                        f"in the {self.bot.group_short_name} Discord Server"
                    ),
                    filename="channels_server_stats.png",
                    description=(
                        "Bar chart of the number of messages sent in different text channels "
                        f"in the {self.bot.group_short_name} Discord server."
                    ),
                ),
            ],
        )

    @stats.command(
        name="self", description="Displays stats about the number of messages you have sent."
    )
    @CommandChecks.check_interaction_user_in_main_guild
    async def user_stats(self, ctx: "TeXBotApplicationContext") -> None:
        """
        Definition & callback response of the "user_stats" command.

        The "user_stats" command sends a graph of the stats about messages sent by the given
        member.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        interaction_member: discord.Member = await self.bot.get_main_guild_member(ctx.user)
        guest_role: discord.Role = await self.bot.guest_role

        if guest_role not in interaction_member.roles:
            await self.command_send_error(
                ctx,
                message=(
                    "You must be inducted as a guest member "
                    f"of the {self.bot.group_short_name} Discord server "
                    "to use this command."
                ),
            )
            return

        await ctx.defer(ephemeral=True)

        message_counts: dict[str, int] = {"Total": 0}

        channel: discord.TextChannel
        for channel in main_guild.text_channels:
            member_has_access_to_channel: bool = channel.permissions_for(
                guest_role
            ).is_superset(discord.Permissions(send_messages=True))
            if not member_has_access_to_channel:
                continue

            message_counts[f"#{channel.name}"] = 0

            message_history_period: AsyncIterable[discord.Message] = channel.history(
                after=discord.utils.utcnow() - settings["STATISTICS_DAYS"]
            )
            message: discord.Message
            async for message in message_history_period:
                if message.author == ctx.user and not message.author.bot:
                    message_counts[f"#{channel.name}"] += 1
                    message_counts["Total"] += 1

        if math.ceil(max(message_counts.values()) / 15) < 1:
            await self.command_send_error(ctx, message="You have not sent enough messages.")
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            file=plot_bar_chart(
                message_counts,
                x_label="Channel Name",
                y_label=(
                    f"""Number of Messages Sent (in the past {
                        amount_of_time_formatter(settings["STATISTICS_DAYS"].days, "day")
                    })"""
                ),
                title=(
                    "Your Most Active Channels "
                    f"in the {self.bot.group_short_name} Discord Server"
                ),
                filename=f"{ctx.user}_stats.png",
                description=(
                    f"Bar chart of the number of messages sent by {ctx.user} "
                    "in different channels in "
                    f"the {self.bot.group_short_name} Discord server."
                ),
            ),
        )

    @stats.command(
        name="left-members",
        description=f"Displays the stats about members that have left {_DISCORD_SERVER_NAME}",
    )
    async def left_member_stats(self, ctx: "TeXBotApplicationContext") -> None:
        """
        Definition & callback response of the "left_member_stats" command.

        The "left_member_stats" command sends a graph of the stats about the roles that members
        had when they left your group's Discord guild.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild

        await ctx.defer(ephemeral=True)

        left_member_counts: dict[str, int] = {
            "Total": await LeftDiscordMember.objects.acount()
        }

        role_name: str
        for role_name in settings["STATISTICS_ROLES"]:
            if discord.utils.get(main_guild.roles, name=role_name):
                left_member_counts[f"@{role_name}"] = 0

        left_member: LeftDiscordMember
        async for left_member in LeftDiscordMember.objects.all():
            for left_member_role in left_member.roles:
                if left_member_role not in left_member_counts:
                    continue

                is_committee_role: bool = left_member_role == "@Committee"
                if is_committee_role and "@Committee-Elect" in left_member.roles:
                    continue

                if left_member_role == "@Guest" and "@Member" in left_member.roles:
                    continue

                left_member_counts[left_member_role] += 1

        if math.ceil(max(left_member_counts.values()) / 15) < 1:
            await self.command_send_error(
                ctx, message="Not enough data about members that have left the server."
            )
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            file=plot_bar_chart(
                left_member_counts,
                x_label="Role Name",
                y_label=(
                    "Number of Members that have left "
                    f"the {self.bot.group_short_name} Discord Server"
                ),
                title=(
                    "Most Common Roles that Members had when they left "
                    f"the {self.bot.group_short_name} Discord Server"
                ),
                filename="left_members_stats.png",
                description=(
                    "Bar chart of the number of members with different roles "
                    f"that have left the {self.bot.group_short_name} Discord server."
                ),
                extra_text=(
                    "Members that left with multiple roles "
                    "are counted once for each role "
                    "(except for @Member vs @Guest & @Committee vs @Committee-Elect)"
                ),
            ),
        )

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_leave(self, member: discord.Member) -> None:
        """Update the stats of the roles that members had when they left your Discord guild."""
        if member.guild != self.bot.main_guild or member.bot:
            return

        await LeftDiscordMember.objects.acreate(  # type: ignore[misc]
            roles={
                f"@{role.name}"
                for role in member.roles
                if role.name.lower().strip("@").strip() != "everyone"
            }
        )
