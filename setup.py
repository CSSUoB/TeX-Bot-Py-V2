import logging
import os
import re
from typing import Any

import discord
import dotenv
from discord import Object, Permissions

from exceptions import ImproperlyConfigured

dotenv.load_dotenv()

settings: dict[str, Any] = {
    "DISCORD_BOT_TOKEN": str(os.getenv("DISCORD_BOT_TOKEN"))
}

if not re.match(r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z", settings["DISCORD_BOT_TOKEN"]):
    raise ImproperlyConfigured("DISCORD_BOT_TOKEN must be a valid Discord bot token (see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)")

settings["DISCORD_BOT_APPLICATION_ID"] = str(os.getenv("DISCORD_BOT_APPLICATION_ID"))
if not re.match(r"\A\d{18,19}\Z", settings["DISCORD_BOT_APPLICATION_ID"]):
    raise ImproperlyConfigured("DISCORD_BOT_APPLICATION_ID must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-us/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)")

_str_DISCORD_GUILD_ID = str(os.getenv("DISCORD_GUILD_ID"))
if not re.match(r"\A\d{18,19}\Z", _str_DISCORD_GUILD_ID):
    raise ImproperlyConfigured("DISCORD_GUILD_ID must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)")
settings["DISCORD_GUILD_ID"] = int(_str_DISCORD_GUILD_ID)

try:
    ping_command_easter_egg_probability = 100 * float(os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01"))
except ValueError as e:
    raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be of type float") from e
if not 100 >= ping_command_easter_egg_probability >= 0:
    raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be a value between & including 1 & 0")
settings["PING_COMMAND_EASTER_EGG_WEIGHTS"] = (100 - ping_command_easter_egg_probability, ping_command_easter_egg_probability)

LOG_LEVEL: str = str(os.getenv("LOG_LEVEL", "INFO")).upper()
if LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ImproperlyConfigured("LOG_LEVEL must be one of: \"DEBUG\", \"INFO\", \"WARNING\", \"ERROR\" or \"CRITICAL\"")
# noinspection SpellCheckingInspection
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(levelname)s | %(module)s: %(message)s"
)


def get_oauth_url():
    return discord.utils.oauth_url(
        client_id=settings["DISCORD_BOT_APPLICATION_ID"],
        permissions=Permissions(
            manage_roles=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            read_message_history=True,
            mention_everyone=True,
            add_reactions=True,
            use_slash_commands=True
        ),
        guild=Object(id=settings["DISCORD_GUILD_ID"]),
        scopes={"bot", "applications.commands"},
        disable_guild_select=True
    )
