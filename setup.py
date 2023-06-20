import json
import logging
import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Any, Match

import django
import dotenv
import validators  # type: ignore

from exceptions import ImproperlyConfigured, MessagesJSONFileMissingKey, MessagesJSONFileValueError


TRUE_VALUES: set[str] = {"true", "1", "t", "y", "yes", "on"}
FALSE_VALUES: set[str] = {"false", "0", "f", "n", "no", "off"}


dotenv.load_dotenv()


os.environ["DJANGO_SETTINGS_MODULE"] = "db.settings"
django.setup()


settings: dict[str, Any] = {
    "DISCORD_BOT_TOKEN": str(os.getenv("DISCORD_BOT_TOKEN"))
}

if not re.match(r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z", settings["DISCORD_BOT_TOKEN"]):
    raise ImproperlyConfigured("DISCORD_BOT_TOKEN must be a valid Discord bot token (see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts).")

settings["DISCORD_BOT_APPLICATION_ID"] = str(os.getenv("DISCORD_BOT_APPLICATION_ID", "")) or None
if settings["DISCORD_BOT_APPLICATION_ID"] and not re.match(r"\A\d{17,20}\Z", settings["DISCORD_BOT_APPLICATION_ID"]):
    raise ImproperlyConfigured("DISCORD_BOT_APPLICATION_ID must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-us/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-).")

str_discord_guild_id: str = str(os.getenv("DISCORD_GUILD_ID"))
if not re.match(r"\A\d{17,20}\Z", str_discord_guild_id):
    raise ImproperlyConfigured("DISCORD_GUILD_ID must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id).")
settings["DISCORD_GUILD_ID"] = int(str_discord_guild_id)

settings["DISCORD_LOG_CHANNEL_ID"] = None
str_discord_log_channel_id: str = str(os.getenv("DISCORD_LOG_CHANNEL_ID", ""))
if str_discord_log_channel_id:
    if not re.match(r"\A\d{17,20}\Z", str_discord_log_channel_id):
        raise ImproperlyConfigured("DISCORD_LOG_CHANNEL_ID must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id).")
    settings["DISCORD_LOG_CHANNEL_ID"] = int(str_discord_log_channel_id)


try:
    ping_command_easter_egg_probability: float = 100 * float(os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01"))
except (ValueError, TypeError) as e:
    raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be a float.") from e
if not 100 >= ping_command_easter_egg_probability >= 0:
    raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be a value between & including 1 & 0.")
settings["PING_COMMAND_EASTER_EGG_WEIGHTS"] = (100 - ping_command_easter_egg_probability, ping_command_easter_egg_probability)


path_messages_file_path: Path = Path(str(os.getenv("MESSAGES_FILE_PATH", "messages.json")))
if not path_messages_file_path.is_file():
    raise ImproperlyConfigured("MESSAGES_FILE_PATH must be a path to a file that exists.")
if not path_messages_file_path.suffix == ".json":
    raise ImproperlyConfigured("MESSAGES_FILE_PATH must be a path to a JSON file.")

with open(path_messages_file_path, "r", encoding="utf8") as messages_file:
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
if not re.match(r"\A[A-Fa-f\d]{128,256}\Z", settings["MEMBERS_PAGE_COOKIE"]):
    raise ImproperlyConfigured("MEMBERS_PAGE_COOKIE must be a valid .ASPXAUTH cookie.")


str_send_introduction_reminders: str = str(os.getenv("SEND_INTRODUCTION_REMINDERS", "Once")).lower()
if str_send_introduction_reminders not in {"once", "interval"} | TRUE_VALUES | FALSE_VALUES:
    raise ImproperlyConfigured("SEND_INTRODUCTION_REMINDERS must be one of: \"Once\", \"Interval\" or \"False\".")
if str_send_introduction_reminders in ("once", "interval"):
    settings["SEND_INTRODUCTION_REMINDERS"] = str_send_introduction_reminders
elif str_send_introduction_reminders in TRUE_VALUES:
    settings["SEND_INTRODUCTION_REMINDERS"] = "once"
else:
    settings["SEND_INTRODUCTION_REMINDERS"] = False

match_introduction_reminder_interval: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("INTRODUCTION_REMINDER_INTERVAL", "6h")))
settings["INTRODUCTION_REMINDER_INTERVAL"] = {"hours": 6}
if settings["SEND_INTRODUCTION_REMINDERS"]:
    if not match_introduction_reminder_interval:
        raise ImproperlyConfigured("INTRODUCTION_REMINDER_INTERVAL must contain the interval in any combination of seconds, minutes or hours.")
    settings["INTRODUCTION_REMINDER_INTERVAL"] = {key: float(value) for key, value in match_introduction_reminder_interval.groupdict().items() if value}

str_kick_no_introduction_members: str = str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS", "False")).lower()
if str_kick_no_introduction_members not in TRUE_VALUES | FALSE_VALUES:
    raise ImproperlyConfigured("KICK_NO_INTRODUCTION_MEMBERS must be a boolean value.")
settings["KICK_NO_INTRODUCTION_MEMBERS"] = str_kick_no_introduction_members in TRUE_VALUES

match_kick_no_introduction_members_delay: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS_DELAY", "120h")))
settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = timedelta()
if settings["KICK_NO_INTRODUCTION_MEMBERS"]:
    if not match_kick_no_introduction_members_delay:
        raise ImproperlyConfigured("KICK_NO_INTRODUCTION_MEMBERS_DELAY must contain the delay in any combination of seconds, minutes or hours.")
    settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = timedelta(**{key: float(value) for key, value in match_kick_no_introduction_members_delay.groupdict().items() if value})

str_send_get_roles_reminders: str = str(os.getenv("SEND_GET_ROLES_REMINDERS", "True")).lower()
if str_send_get_roles_reminders not in TRUE_VALUES | FALSE_VALUES:
    raise ImproperlyConfigured("SEND_GET_ROLES_REMINDERS must be a boolean value.")
settings["SEND_GET_ROLES_REMINDERS"] = str_send_get_roles_reminders in TRUE_VALUES

match_get_roles_reminder_interval: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("GET_ROLES_REMINDER_INTERVAL", "24h")))
settings["GET_ROLES_REMINDER_INTERVAL"] = {"hours": 24}
if settings["SEND_GET_ROLES_REMINDERS"]:
    if not match_get_roles_reminder_interval:
        raise ImproperlyConfigured("GET_ROLES_REMINDER_INTERVAL must contain the interval in any combination of seconds, minutes or hours.")
    settings["GET_ROLES_REMINDER_INTERVAL"] = {key: float(value) for key, value in match_get_roles_reminder_interval.groupdict().items() if value}


try:
    float_statistics_days: float = float(os.getenv("STATISTICS_DAYS", 30))
except (ValueError, TypeError) as statistics_days_error:
    raise ImproperlyConfigured("STATISTICS_DAYS must contain the statistics period in days.") from statistics_days_error
settings["STATISTICS_DAYS"] = timedelta(days=float_statistics_days)


try:
    statistics_roles: set[str] = set(filter(None, os.getenv("STATISTICS_ROLES", "").split(",")))
except (ValueError, TypeError) as statistics_roles_error:
    try:
        statistics_roles = {str(role_name) for role_name in filter(None, os.getenv("STATISTICS_ROLES", "").split(","))}
    except (ValueError, TypeError):
        raise ImproperlyConfigured("STATISTICS_ROLES must be a list of the names of roles to check the statistics of.") from statistics_roles_error
settings["STATISTICS_ROLES"] = statistics_roles or {"Committee", "Committee-Elect", "Student Rep", "Member", "Guest", "Server Booster", "Foundation Year", "First Year", "Second Year", "Final Year", "Year In Industry", "Year Abroad", "PGT", "PGR", "Alumnus/Alumna", "Postdoc", "Quiz Victor"}


console_log_level: str = str(os.getenv("CONSOLE_LOG_LEVEL", "INFO")).upper()
if console_log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ImproperlyConfigured("LOG_LEVEL must be one of: \"DEBUG\", \"INFO\", \"WARNING\", \"ERROR\" or \"CRITICAL\"")
# noinspection SpellCheckingInspection
logging.basicConfig(
    level=getattr(logging, console_log_level),
    format="%(levelname)s | %(module)s: %(message)s"
)
