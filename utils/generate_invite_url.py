"""Utility function to generate the URL to invite the bot to a given Discord guild."""


import re
from collections.abc import Sequence

import discord

__all__: Sequence[str] = ("generate_invite_url",)

def generate_invite_url(discord_bot_application_id: str, discord_guild_id: str) -> str:
    """Execute the logic that this util function provides."""
    discord_bot_application_id = str(discord_bot_application_id)
    discord_guild_id = str(discord_guild_id)

    if not discord_guild_id:
        err = "discord_guild_id must be set in the DISCORD_GUILD_ID environment variable"
        raise ValueError(err)

    if not discord_guild_id or not re.match(r"\A\d{17,20}\Z", discord_guild_id):
        err = "discord_guild_id must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
        raise ValueError(err)

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
            ban_members=True,
            manage_channels=True,
            view_audit_log=True
        ),
        guild=discord.Object(id=discord_guild_id),
        scopes=("bot", "applications.commands"),
        disable_guild_select=True
    )
