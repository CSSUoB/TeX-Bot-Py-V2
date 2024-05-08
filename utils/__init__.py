"""Utility classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "CommandChecks",
    "MessageSenderComponent",
    "SuppressTraceback",
    "TeXBot",
    "TeXBotBaseCog",
    "TeXBotApplicationContext",
    "TeXBotAutocompleteContext",
    "generate_invite_url",
)


import discord

from utils.command_checks import CommandChecks
from utils.message_sender_components import MessageSenderComponent
from utils.suppress_traceback import SuppressTraceback
from utils.tex_bot import TeXBot
from utils.tex_bot_base_cog import TeXBotBaseCog
from utils.tex_bot_contexts import TeXBotApplicationContext, TeXBotAutocompleteContext


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
            view_audit_log=True,
        ),
        guild=discord.Object(id=discord_guild_id),
        scopes=("bot", "applications.commands"),
        disable_guild_select=True,
    )

def is_user_inducted(guild: discord.Guild, user: discord.Member) -> bool:
    """
    Util method to check if the supplied user has been inducted.

    Returns true if the user has a role that is considered to be inducted.
    Which roles are considered to be inducted should be specified in the config.
    """
    news_role: discord.Role | None = discord.utils.get(
        guild.roles,
        name="@News",
    )

    return any(role is not news_role for role in user.roles)
