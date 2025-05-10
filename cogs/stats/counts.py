"""Contains methods relating to counting messages in channels."""

from typing import TYPE_CHECKING

import discord

from config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Mapping, Sequence


__all__: "Sequence[str]" = ("get_channel_message_counts", "get_server_message_counts")


async def get_channel_message_counts(channel: discord.TextChannel) -> dict[str, int]:
    """
    Get the message counts for each role in the given channel.

    The message counts are stored in a mapping with the role name (prefixed by `@`) as the key
    and the number of messages sent by users with that role as the value.
    The mapping also includes a "Total" key for the total number of messages.
    """
    message_counts: dict[str, int] = {"Total": 0}

    role_name: str
    for role_name in settings["STATISTICS_ROLES"]:
        if discord.utils.get(channel.guild.roles, name=role_name):
            message_counts[f"@{role_name}"] = 0

    message_history_period: AsyncIterable[discord.Message] = channel.history(
        after=discord.utils.utcnow() - settings["STATISTICS_DAYS"],
    )
    message: discord.Message
    async for message in message_history_period:
        if message.author.bot:
            continue

        message_counts["Total"] += 1

        if isinstance(message.author, discord.User):
            continue

        author_role_names: set[str] = {
            author_role.name for author_role in message.author.roles
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

    return message_counts


async def get_server_message_counts(
    guild: discord.Guild, *, guest_role: discord.Role
) -> dict[str, dict[str, int]]:
    """
    Get the message counts for each channel in the given server.

    The message counts are stored in a mapping. It contains a key "roles" which is
    a mapping of role names (prefixed by `@`) to the message counts
    for each role across the entire server.
    The mapping also contains a key "channels" which is a mapping with the channel
    name as a key and the number of messages sent in that channel as the value.
    The "roles" sub-mapping also includes a "Total" key for the total number of messages.
    """
    message_counts: dict[str, dict[str, int]] = {
        "roles": {"Total": 0},
        "channels": {},
    }

    role_name: str
    for role_name in settings["STATISTICS_ROLES"]:
        if discord.utils.get(guild.roles, name=role_name):
            message_counts["roles"][f"@{role_name}"] = 0

    channel: discord.TextChannel
    for channel in guild.text_channels:
        member_has_access_to_channel: bool = channel.permissions_for(
            guest_role,
        ).is_superset(
            discord.Permissions(send_messages=True),
        )
        if not member_has_access_to_channel:
            continue

        message_counts["channels"][f"#{channel.name}"] = 0

        message_history_period: AsyncIterable[discord.Message] = channel.history(
            after=discord.utils.utcnow() - settings["STATISTICS_DAYS"],
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
                author_role.name for author_role in message.author.roles
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

    return message_counts
