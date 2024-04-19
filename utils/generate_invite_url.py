"""Utility function to generate the URL to invite the bot to a given Discord guild."""

from collections.abc import Sequence

__all__: Sequence[str] = ("generate_invite_url",)

import discord


def generate_invite_url(discord_bot_application_id: int, discord_guild_id: int) -> str:
    """Execute the logic that this util function provides."""
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
