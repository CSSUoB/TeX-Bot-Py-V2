"""Utility classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "AllChannelTypes",
    "CommandChecks",
    "generate_invite_url",
    "is_member_inducted",
    "is_running_in_async",
    "MessageSavingSenderComponent",
    "SuppressTraceback",
    "TeXBot",
    "TeXBotApplicationContext",
    "TeXBotAutocompleteContext",
    "TeXBotBaseCog",
)


import asyncio

import discord

from .command_checks import CommandChecks
from .message_sender_components import MessageSavingSenderComponent
from .suppress_traceback import SuppressTraceback
from .tex_bot import TeXBot
from .tex_bot_base_cog import TeXBotBaseCog
from .tex_bot_contexts import TeXBotApplicationContext, TeXBotAutocompleteContext

type AllChannelTypes = (
    discord.VoiceChannel
    | discord.StageChannel
    | discord.TextChannel
    | discord.ForumChannel
    | discord.CategoryChannel
    | None
)


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
            moderate_members=True,
        ),
        guild=discord.Object(id=discord_guild_id),
        scopes=("bot", "applications.commands"),
        disable_guild_select=True,
    )


def is_member_inducted(member: discord.Member) -> bool:
    """
    Util method to check if the supplied member has been inducted.

    Returns True if the member has any role other than "@News".
    The set of ignored roles is a tuple to make the set easily expandable.
    """
    return any(
        role.name.lower().strip("@ \n\t") not in ("news",) for role in member.roles
    )


def is_running_in_async() -> bool:
    """Determine whether the current context is asynchronous or not."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    else:
        return True
