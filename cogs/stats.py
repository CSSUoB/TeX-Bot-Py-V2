"""Contains cog classes for any stats interactions."""

import logging
import math
import re

import discord

import utils
from cogs._utils import TeXBotApplicationContext, TeXBotCog
from config import settings
from db.core.models import LeftMember
from exceptions import GuestRoleDoesNotExist, GuildDoesNotExist


class StatsCommandsCog(TeXBotCog):
    """Cog class that defines the "/stats" command group and its command call-back methods."""

    stats: discord.SlashCommandGroup = discord.SlashCommandGroup(
        "stats",
        "Various statistics about the CSS Discord server"
    )

    # noinspection SpellCheckingInspection
    @stats.command(
        name="channel",
        description="Displays the stats for the current/a given channel."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="channel",
        description="The channel to display the stats for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(
            TeXBotCog.autocomplete_get_text_channels  # type: ignore[arg-type]
        ),
        required=False,
        parameter_name="str_channel_id"
    )
    async def channel_stats(self, ctx: TeXBotApplicationContext, str_channel_id: str) -> None:
        """
        Definition & callback response of the "channel_stats" command.

        The "channel_stats" command sends a graph of the stats about messages sent in the given
        channel.
        """
        channel_id: int = ctx.channel_id

        if str_channel_id:
            if not re.match(r"\A\d{17,20}\Z", str_channel_id):
                await self.send_error(
                    ctx,
                    message=f"\"{str_channel_id}\" is not a valid channel ID."
                )
                return

            channel_id = int(str_channel_id)

        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        channel: discord.TextChannel | None = discord.utils.get(
            guild.text_channels,
            id=channel_id
        )
        if not channel:
            await self.send_error(
                ctx,
                message=f"Text channel with ID \"{channel_id}\" does not exist."
            )
            return

        await ctx.defer(ephemeral=True)

        message_counts: dict[str, int] = {"Total": 0}

        role_name: str
        for role_name in settings["STATISTICS_ROLES"]:
            if discord.utils.get(guild.roles, name=role_name):
                message_counts[f"@{role_name}"] = 0

        message_history_period: discord.iterators.HistoryIterator = channel.history(
            after=discord.utils.utcnow() - settings["STATISTICS_DAYS"]
        )
        message: discord.Message
        async for message in message_history_period:
            if message.author.bot:
                continue

            message_counts["Total"] += 1

            if isinstance(message.author, discord.User):
                continue

            author_role_names: set[str] = {
                author_role.name
                for author_role
                in message.author.roles
            }

            author_role_name: str
            for author_role_name in author_role_names:
                if f"@{author_role_name}" in message_counts:
                    is_author_role_name: bool = author_role_name == "Committee"
                    if is_author_role_name and "Committee-Elect" in author_role_names:
                        continue

                    if author_role_name == "Guest" and "Member" in author_role_names:
                        continue

                    message_counts[f"@{author_role_name}"] += 1

        if math.ceil(max(message_counts.values()) / 15) < 1:
            await self.send_error(
                ctx,
                message="There are not enough messages sent in this channel."
            )
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            file=utils.plot_bar_chart(
                message_counts,
                xlabel="Role Name",
                ylabel=(
                    f"""Number of Messages Sent (in the past {
                        utils.amount_of_time_formatter(
                            settings["STATISTICS_DAYS"].days,
                            "day"
                        )
                    })"""
                ),
                title=f"Most Active Roles in #{channel.name}",
                filename=f"{channel.name}_channel_stats.png",
                description=(
                    "Bar chart of the number of messages"
                    f" sent by different roles in {channel.mention}."
                ),
                extra_text=(
                    "Messages sent by members with multiple roles are counted once"
                    " for each role"
                    " (except for @Member vs @Guest & @Committee vs @Committee-Elect)"
                )
            )
        )

    @stats.command(
        name="server",
        description="Displays the stats for the whole of the CSS Discord server."
    )
    async def server_stats(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "server_stats" command.

        The "server_stats" command sends a graph of the stats about messages sent in the whole
        of the CSS Discord server.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        guest_role: discord.Role = await self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                logging_message=GuestRoleDoesNotExist()
            )
            return

        await ctx.defer(ephemeral=True)

        message_counts: dict[str, dict[str, int]] = {
            "roles": {"Total": 0},
            "channels": {}
        }

        role_name: str
        for role_name in settings["STATISTICS_ROLES"]:
            if discord.utils.get(guild.roles, name=role_name):
                message_counts["roles"][f"@{role_name}"] = 0

        channel: discord.TextChannel
        for channel in guild.text_channels:
            member_has_access_to_channel: bool = channel.permissions_for(
                guest_role
            ).is_superset(
                discord.Permissions(send_messages=True)
            )
            if not member_has_access_to_channel:
                continue

            message_counts["channels"][f"#{channel.name}"] = 0

            message_history_period: discord.iterators.HistoryIterator = channel.history(
                after=discord.utils.utcnow() - settings["STATISTICS_DAYS"]
            )
            message: discord.Message
            async for message in message_history_period:
                if message.author.bot:
                    continue

                message_counts["channels"][f"#{channel.name}"] += 1
                message_counts["roles"]["Total"] += 1

                if isinstance(message.author, discord.User):
                    continue

                author_role_names: set[str] = {
                    author_role.name
                    for author_role
                    in message.author.roles
                }

                author_role_name: str
                for author_role_name in author_role_names:
                    if f"@{author_role_name}" in message_counts["roles"]:
                        is_author_role_committee: bool = author_role_name == "Committee"
                        if is_author_role_committee and "Committee-Elect" in author_role_names:
                            continue

                        if author_role_name == "Guest" and "Member" in author_role_names:
                            continue

                        message_counts["roles"][f"@{author_role_name}"] += 1

        too_few_roles_stats: bool = math.ceil(max(message_counts["roles"].values()) / 15) < 1
        too_few_channels_stats: bool = math.ceil(
            max(message_counts["channels"].values()) / 15
        ) < 1
        if too_few_roles_stats or too_few_channels_stats:
            await self.send_error(ctx, message="There are not enough messages sent.")
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            files=[
                utils.plot_bar_chart(
                    message_counts["roles"],
                    xlabel="Role Name",
                    ylabel=(
                        f"""Number of Messages Sent (in the past {
                        utils.amount_of_time_formatter(
                            settings["STATISTICS_DAYS"].days,
                            "day"
                        )
                        })"""
                    ),
                    title="Most Active Roles in the CSS Discord Server",
                    filename="roles_server_stats.png",
                    description=(
                        "Bar chart of the number of messages sent by different roles"
                        " in the CSS Discord server."
                    ),
                    extra_text=(
                        "Messages sent by members with multiple roles are counted once"
                        " for each role"
                        " (except for @Member vs @Guest & @Committee vs @Committee-Elect)"
                    )
                ),
                utils.plot_bar_chart(
                    message_counts["channels"],
                    xlabel="Channel Name",
                    ylabel=(
                        f"""Number of Messages Sent (in the past {
                            utils.amount_of_time_formatter(
                                settings["STATISTICS_DAYS"].days,
                                "day"
                            )
                        })"""
                    ),
                    title="Most Active Channels in the CSS Discord Server",
                    filename="channels_server_stats.png",
                    description=(
                        "Bar chart of the number of messages sent in different text channels"
                        " in the CSS Discord server."
                    )
                ),
            ]
        )

    @stats.command(
        name="self",
        description="Displays stats about the number of messages you have sent."
    )
    async def user_stats(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "user_stats" command.

        The "user_stats" command sends a graph of the stats about messages sent by the given
        member.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        guest_role: discord.Role = await self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                logging_message=GuestRoleDoesNotExist()
            )
            return

        if guest_role not in interaction_member.roles:
            await self.send_error(
                ctx,
                message=(
                    "You must be inducted as guest member of the CSS Discord server"
                    " to use this command."
                )
            )
            return

        await ctx.defer(ephemeral=True)

        message_counts: dict[str, int] = {"Total": 0}

        channel: discord.TextChannel
        for channel in guild.text_channels:
            member_has_access_to_channel: bool = channel.permissions_for(
                guest_role
            ).is_superset(
                discord.Permissions(send_messages=True)
            )
            if not member_has_access_to_channel:
                continue

            message_counts[f"#{channel.name}"] = 0

            message_history_period: discord.iterators.HistoryIterator = channel.history(
                after=discord.utils.utcnow() - settings["STATISTICS_DAYS"]
            )
            message: discord.Message
            async for message in message_history_period:
                if message.author == ctx.user and not message.author.bot:
                    message_counts[f"#{channel.name}"] += 1
                    message_counts["Total"] += 1

        if math.ceil(max(message_counts.values()) / 15) < 1:
            await self.send_error(
                ctx,
                message="You have not sent enough messages."
            )
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            file=utils.plot_bar_chart(
                message_counts,
                xlabel="Channel Name",
                ylabel=(
                    f"""Number of Messages Sent (in the past {
                        utils.amount_of_time_formatter(
                            settings["STATISTICS_DAYS"].days,
                            "day"
                        )
                    })"""
                ),
                title="Your Most Active Channels in the CSS Discord Server",
                filename=f"{ctx.user}_stats.png",
                description=(
                    f"Bar chart of the number of messages sent by {ctx.user}"
                    " in different channels in the CSS Discord server."
                )
            )
        )

    # noinspection SpellCheckingInspection
    @stats.command(
        name="leftmembers",
        description="Displays the stats about members that have left the CSS Discord server."
    )
    async def left_member_stats(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "left_member_stats" command.

        The "left_member_stats" command sends a graph of the stats about the roles that members
        had when they left the CSS Discord server.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        await ctx.defer(ephemeral=True)

        left_member_counts: dict[str, int] = {
            "Total": await LeftMember.objects.acount()
        }

        role_name: str
        for role_name in settings["STATISTICS_ROLES"]:
            if discord.utils.get(guild.roles, name=role_name):
                left_member_counts[f"@{role_name}"] = 0

        left_member: LeftMember
        async for left_member in LeftMember.objects.all():
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
            await self.send_error(
                ctx,
                message="Not enough data about members that have left the server."
            )
            return

        await ctx.respond(":point_down:Your stats graph is shown below:point_down:")

        await ctx.channel.send(
            f"**{ctx.user.display_name}** used `/{ctx.command}`",
            file=utils.plot_bar_chart(
                left_member_counts,
                xlabel="Role Name",
                ylabel="Number of Members that have left the CSS Discord Server",
                title=(
                    "Most Common Roles that Members had when they left the CSS Discord Server"
                ),
                filename="left_members_stats.png",
                description=(
                    "Bar chart of the number of members with different roles"
                    " that have left the CSS Discord server."
                ),
                extra_text=(
                    "Members that left with multiple roles"
                    " are counted once for each role"
                    " (except for @Member vs @Guest & @Committee vs @Committee-Elect)"
                )
            )
        )

    @TeXBotCog.listener()
    async def on_member_leave(self, member: discord.Member) -> None:
        """Update the stats of the roles that members had when they left the Discord server."""
        try:
            css_guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        if member.guild != css_guild or member.bot:
            return

        await LeftMember.objects.acreate(
            roles={f"@{role.name}" for role in member.roles if role.name != "@everyone"}
        )
