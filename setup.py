import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Match

import django  # type: ignore
import dotenv
import validators  # type: ignore
from django.core import management  # type: ignore

from exceptions import ImproperlyConfigured, MessagesJSONFileMissingKey, MessagesJSONFileValueError


TRUE_VALUES: set[str] = {"true", "1", "t", "y", "yes", "on"}
FALSE_VALUES: set[str] = {"false", "0", "f", "n", "no", "off"}


dotenv.load_dotenv()


os.environ["DJANGO_SETTINGS_MODULE"] = "db.settings"
django.setup()
management.call_command("makemigrations")
management.call_command("makemigrations", "core")
management.call_command("migrate")


settings: dict[str, Any] = {
    "DISCORD_BOT_TOKEN": str(os.getenv("DISCORD_BOT_TOKEN"))
}

if not re.match(r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z", settings["DISCORD_BOT_TOKEN"]):
    raise ImproperlyConfigured("DISCORD_BOT_TOKEN must be a valid Discord bot token (see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts).")

settings["DISCORD_BOT_APPLICATION_ID"] = str(os.getenv("DISCORD_BOT_APPLICATION_ID"))
if not re.match(r"\A\d{17,20}\Z", settings["DISCORD_BOT_APPLICATION_ID"]):
    raise ImproperlyConfigured("DISCORD_BOT_APPLICATION_ID must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-us/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-).")

_str_DISCORD_GUILD_ID = str(os.getenv("DISCORD_GUILD_ID"))
if not re.match(r"\A\d{17,20}\Z", _str_DISCORD_GUILD_ID):
    raise ImproperlyConfigured("DISCORD_GUILD_ID must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id).")
settings["DISCORD_GUILD_ID"] = int(_str_DISCORD_GUILD_ID)

try:
    ping_command_easter_egg_probability = 100 * float(os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01"))
except ValueError as e:
    raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be a float.") from e
if not 100 >= ping_command_easter_egg_probability >= 0:
    raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be a value between & including 1 & 0.")
settings["PING_COMMAND_EASTER_EGG_WEIGHTS"] = (100 - ping_command_easter_egg_probability, ping_command_easter_egg_probability)

_path_MESSAGES_FILE_PATH = Path(str(os.getenv("MESSAGES_FILE_PATH", "messages.json")))
if not _path_MESSAGES_FILE_PATH.is_file():
    raise ImproperlyConfigured("MESSAGES_FILE_PATH must be a path to a file that exists.")
if not _path_MESSAGES_FILE_PATH.suffix == ".json":
    raise ImproperlyConfigured("MESSAGES_FILE_PATH must be a path to a JSON file.")

with open(_path_MESSAGES_FILE_PATH, "r", encoding="utf8") as messages_file:
    try:
        messages_dict: dict = json.load(messages_file)
    except json.JSONDecodeError as messages_file_error:
        raise ImproperlyConfigured("Messages JSON file must contain a JSON string that can be decoded into a Python dict object.") from messages_file_error

if "welcome_messages" not in messages_dict:
    raise MessagesJSONFileMissingKey(missing_key="welcome_messages")
if not isinstance(messages_dict["welcome_messages"], list) or not messages_dict["welcome_messages"]:
    raise MessagesJSONFileValueError(dict_key="welcome_messages", invalid_value=messages_dict["welcome_messages"])
settings["WELCOME_MESSAGES"] = messages_dict["welcome_messages"]

if "roles_messages" not in messages_dict:
    raise MessagesJSONFileMissingKey(missing_key="roles_messages")
if not isinstance(messages_dict["roles_messages"], list) or not messages_dict["roles_messages"]:
    raise MessagesJSONFileValueError(dict_key="roles_messages", invalid_value=messages_dict["roles_messages"])
settings["ROLES_MESSAGES"] = messages_dict["roles_messages"]

settings["MEMBERS_PAGE_URL"] = str(os.getenv("MEMBERS_PAGE_URL"))
if not validators.url(settings["MEMBERS_PAGE_URL"]):
    raise ImproperlyConfigured("MEMBERS_PAGE_URL must be a valid URL.")

settings["MEMBERS_PAGE_COOKIE"] = str(os.getenv("MEMBERS_PAGE_COOKIE"))
if not re.match(r"\A[A-Fa-f\d]{200}\Z", settings["MEMBERS_PAGE_COOKIE"]):
    raise ImproperlyConfigured("MEMBERS_PAGE_COOKIE must be a valid .ASPXAUTH cookie.")

_str_SEND_INTRODUCTION_REMINDERS = str(os.getenv("SEND_INTRODUCTION_REMINDERS", "True")).lower()
if _str_SEND_INTRODUCTION_REMINDERS not in TRUE_VALUES | FALSE_VALUES:
    raise ImproperlyConfigured("SEND_INTRODUCTION_REMINDERS must be a boolean value.")
settings["SEND_INTRODUCTION_REMINDERS"] = _str_SEND_INTRODUCTION_REMINDERS in TRUE_VALUES

_match_INTRODUCTION_REMINDER_INTERVAL: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("INTRODUCTION_REMINDER_INTERVAL", "6h")))
settings["INTRODUCTION_REMINDER_INTERVAL"] = {"hours": 100}
if settings["SEND_INTRODUCTION_REMINDERS"]:
    if not _match_INTRODUCTION_REMINDER_INTERVAL:
        raise ImproperlyConfigured("INTRODUCTION_REMINDER_INTERVAL must contain the interval in any combination of seconds, minutes or hours.")
    settings["INTRODUCTION_REMINDER_INTERVAL"] = {key: float(value) for key, value in _match_INTRODUCTION_REMINDER_INTERVAL.groupdict().items() if value}

_str_KICK_NO_INTRODUCTION_MEMBERS = str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS", "True")).lower()
if _str_KICK_NO_INTRODUCTION_MEMBERS not in TRUE_VALUES | FALSE_VALUES:
    raise ImproperlyConfigured("KICK_NO_INTRODUCTION_MEMBERS must be a boolean value.")
settings["KICK_NO_INTRODUCTION_MEMBERS"] = _str_KICK_NO_INTRODUCTION_MEMBERS in TRUE_VALUES

_match_KICK_NO_INTRODUCTION_MEMBERS_DELAY: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS_DELAY", "120h")))
settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = {"hours": 999}
if settings["KICK_NO_INTRODUCTION_MEMBERS"]:
    if not _match_KICK_NO_INTRODUCTION_MEMBERS_DELAY:
        raise ImproperlyConfigured("KICK_NO_INTRODUCTION_MEMBERS_DELAY must contain the delay in any combination of seconds, minutes or hours.")
    settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = {key: float(value) for key, value in _match_KICK_NO_INTRODUCTION_MEMBERS_DELAY.groupdict().items() if value}

_match_GET_ROLES_REMINDER_INTERVAL: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("GET_ROLES_REMINDER_INTERVAL", "24h")))
if not _match_GET_ROLES_REMINDER_INTERVAL:
    raise ImproperlyConfigured("GET_ROLES_REMINDER_INTERVAL must contain the interval in any combination of seconds, minutes or hours.")
settings["GET_ROLES_REMINDER_INTERVAL"] = {key: float(value) for key, value in _match_GET_ROLES_REMINDER_INTERVAL.groupdict().items() if value}

LOG_LEVEL: str = str(os.getenv("LOG_LEVEL", "INFO")).upper()
if LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ImproperlyConfigured("LOG_LEVEL must be one of: \"DEBUG\", \"INFO\", \"WARNING\", \"ERROR\" or \"CRITICAL\"")
# noinspection SpellCheckingInspection
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(levelname)s | %(module)s: %(message)s"
)
