"""
    Settings values that are imported from the .env file or the current
    environment variables. These values are used to configure the functionality
    of the bot at run-time.
"""

import json
import logging
import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Match, Sequence

import django
import dotenv
import validators

from exceptions import ImproperlyConfigured, MessagesJSONFileMissingKey, MessagesJSONFileValueError


TRUE_VALUES: set[str] = {"true", "1", "t", "y", "yes", "on"}
FALSE_VALUES: set[str] = {"false", "0", "f", "n", "no", "off"}


class SettingsMeta(type):
    """
        The metaclass that defines how to access the values of the settings
        class (via class attributes & item lookup).
    """

    def __getattr__(self, item: str) -> Any:
        if "_settings" not in self.__dict__ or not isinstance(self._settings, dict):
            raise AttributeError(f"A \"_settings\" dictionary must be declared on the {self.__name__} class in order to access the settings values.")

        setup_env_variables()

        if item in self._settings:
            return self._settings[item]
        else:
            raise AttributeError(f"type object '{self.__name__}' has no attribute '{item}'")

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError as getattr_error:
            if "\"_settings\" dictionary must be declared" in "".join(getattr_error.args):  # NOTE: Continue to raise an AttributeError if it was originally caused by the _settings dictionary not existing
                raise
            else:
                raise KeyError(item)  # NOTE: Raise a KeyError instead, if the AttributeError was caused by the key not existing in the _settings dictionary


class Settings(metaclass=SettingsMeta):
    """
        The settings class that provides access to all settings values. Can be
        accessed via key (like a dictionary) or via class attribute.
    """

    _is_env_variables_setup: bool = False
    _is_django_setup: bool = False
    _settings: dict[str, Any] = {}

    @classmethod
    def setup_env_variables(cls) -> None:
        """
            Setup function to load the values from the .env file/the current
            environment variables into the settings dictionary after validating the
            input values/defining defaults.
        """

        if not cls._is_env_variables_setup:
            dotenv.load_dotenv()

            discord_bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
            if not discord_bot_token or not re.match(r"\A([A-Za-z0-9]{24,26})\.([A-Za-z0-9]{6})\.([A-Za-z0-9_-]{27,38})\Z", discord_bot_token):
                raise ImproperlyConfigured("DISCORD_BOT_TOKEN must be a valid Discord bot token (see https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts).")
            cls._settings["DISCORD_BOT_TOKEN"] = discord_bot_token

            discord_guild_id: str = os.getenv("DISCORD_GUILD_ID", "")
            if not discord_guild_id or not re.match(r"\A\d{17,20}\Z", discord_guild_id):
                raise ImproperlyConfigured("DISCORD_GUILD_ID must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id).")
            cls._settings["DISCORD_GUILD_ID"] = int(discord_guild_id)

            cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = os.getenv("DISCORD_LOG_CHANNEL_WEBHOOK_URL", "")
            if cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] and (not validators.url(cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]) or not cls._settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"].startswith("https://discord.com/api/webhooks/")):
                raise ImproperlyConfigured("DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL that points to a discord channel where logs should be displayed.")

            try:
                cls._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] = 100 * float(os.getenv("PING_COMMAND_EASTER_EGG_PROBABILITY", "0.01"))
            except ValueError as ping_command_easter_egg_probability_error:
                raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be a float.") from ping_command_easter_egg_probability_error
            if not 100 >= cls._settings["PING_COMMAND_EASTER_EGG_PROBABILITY"] >= 0:
                raise ImproperlyConfigured("PING_COMMAND_EASTER_EGG_PROBABILITY must be a value between & including 1 & 0.")

            messages_file_path: Path = Path(os.getenv("MESSAGES_FILE_PATH", "messages.json"))
            if not messages_file_path.is_file():
                raise ImproperlyConfigured("MESSAGES_FILE_PATH must be a path to a file that exists.")
            if not messages_file_path.suffix == ".json":
                raise ImproperlyConfigured("MESSAGES_FILE_PATH must be a path to a JSON file.")

            with open(messages_file_path, "r", encoding="utf8") as messages_file:
                try:
                    messages_dict: dict = json.load(messages_file)
                except json.JSONDecodeError as messages_file_error:
                    raise ImproperlyConfigured("Messages JSON file must contain a JSON string that can be decoded into a Python dict object.") from messages_file_error

            if "welcome_messages" not in messages_dict:
                raise MessagesJSONFileMissingKey(missing_key="welcome_messages")
            if not isinstance(messages_dict["welcome_messages"], list) or not messages_dict["welcome_messages"]:
                raise MessagesJSONFileValueError(dict_key="welcome_messages", invalid_value=messages_dict["welcome_messages"])
            cls._settings["WELCOME_MESSAGES"] = messages_dict["welcome_messages"]

            if "roles_messages" not in messages_dict:
                raise MessagesJSONFileMissingKey(missing_key="roles_messages")
            if not isinstance(messages_dict["roles_messages"], list) or not messages_dict["roles_messages"]:
                raise MessagesJSONFileValueError(dict_key="roles_messages", invalid_value=messages_dict["roles_messages"])
            cls._settings["ROLES_MESSAGES"] = messages_dict["roles_messages"]

            cls._settings["MEMBERS_PAGE_URL"] = os.getenv("MEMBERS_PAGE_URL", "")
            if not cls._settings["MEMBERS_PAGE_URL"] or not validators.url(cls._settings["MEMBERS_PAGE_URL"]):
                raise ImproperlyConfigured("MEMBERS_PAGE_URL must be a valid URL.")

            cls._settings["MEMBERS_PAGE_COOKIE"] = os.getenv("MEMBERS_PAGE_COOKIE", "")
            if not cls._settings["MEMBERS_PAGE_COOKIE"] or not re.match(r"\A[A-Fa-f\d]{128,256}\Z", cls._settings["MEMBERS_PAGE_COOKIE"]):
                raise ImproperlyConfigured("MEMBERS_PAGE_COOKIE must be a valid .ASPXAUTH cookie.")

            send_introduction_reminders: str = str(os.getenv("SEND_INTRODUCTION_REMINDERS", "Once")).lower()
            if send_introduction_reminders not in {"once", "interval"} | TRUE_VALUES | FALSE_VALUES:
                raise ImproperlyConfigured("SEND_INTRODUCTION_REMINDERS must be one of: \"Once\", \"Interval\" or \"False\".")
            if send_introduction_reminders in ("once", "interval"):
                cls._settings["SEND_INTRODUCTION_REMINDERS"] = send_introduction_reminders
            elif send_introduction_reminders in TRUE_VALUES:
                cls._settings["SEND_INTRODUCTION_REMINDERS"] = "once"
            else:
                cls._settings["SEND_INTRODUCTION_REMINDERS"] = False

            introduction_reminder_interval: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("INTRODUCTION_REMINDER_INTERVAL", "6h")))
            cls._settings["INTRODUCTION_REMINDER_INTERVAL"] = {"hours": 6}
            if cls._settings["SEND_INTRODUCTION_REMINDERS"]:
                if not introduction_reminder_interval:
                    raise ImproperlyConfigured("INTRODUCTION_REMINDER_INTERVAL must contain the interval in any combination of seconds, minutes or hours.")
                cls._settings["INTRODUCTION_REMINDER_INTERVAL"] = {key: float(value) for key, value in introduction_reminder_interval.groupdict().items() if value}

            kick_no_introduction_members: str = str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS", "False")).lower()
            if kick_no_introduction_members not in TRUE_VALUES | FALSE_VALUES:
                raise ImproperlyConfigured("KICK_NO_INTRODUCTION_MEMBERS must be a boolean value.")
            cls._settings["KICK_NO_INTRODUCTION_MEMBERS"] = kick_no_introduction_members in TRUE_VALUES

            kick_no_introduction_members_delay: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?(?:(?P<days>(?:\d*\.)?\d+)d)?(?:(?P<weeks>(?:\d*\.)?\d+)w)?\Z", str(os.getenv("KICK_NO_INTRODUCTION_MEMBERS_DELAY", "5d")))
            cls._settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = timedelta()
            if cls._settings["KICK_NO_INTRODUCTION_MEMBERS"]:
                if not kick_no_introduction_members_delay:
                    raise ImproperlyConfigured("KICK_NO_INTRODUCTION_MEMBERS_DELAY must contain the delay in any combination of seconds, minutes, hours, days or weeks.")
                cls._settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] = timedelta(**{key: float(value) for key, value in kick_no_introduction_members_delay.groupdict().items() if value})
                if cls._settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"] <= timedelta(days=1):
                    raise ImproperlyConfigured("KICK_NO_INTRODUCTION_MEMBERS_DELAY must be greater than 1 day.")

            send_get_roles_reminders: str = str(os.getenv("SEND_GET_ROLES_REMINDERS", "True")).lower()
            if send_get_roles_reminders not in TRUE_VALUES | FALSE_VALUES:
                raise ImproperlyConfigured("SEND_GET_ROLES_REMINDERS must be a boolean value.")
            cls._settings["SEND_GET_ROLES_REMINDERS"] = send_get_roles_reminders in TRUE_VALUES

            get_roles_reminder_interval: Match | None = re.match(r"\A(?:(?P<seconds>(?:\d*\.)?\d+)s)?(?:(?P<minutes>(?:\d*\.)?\d+)m)?(?:(?P<hours>(?:\d*\.)?\d+)h)?\Z", str(os.getenv("GET_ROLES_REMINDER_INTERVAL", "24h")))
            cls._settings["GET_ROLES_REMINDER_INTERVAL"] = {"hours": 24}
            if cls._settings["SEND_GET_ROLES_REMINDERS"]:
                if not get_roles_reminder_interval:
                    raise ImproperlyConfigured("GET_ROLES_REMINDER_INTERVAL must contain the interval in any combination of seconds, minutes or hours.")
                cls._settings["GET_ROLES_REMINDER_INTERVAL"] = {key: float(value) for key, value in get_roles_reminder_interval.groupdict().items() if value}

            try:
                statistics_days: float = float(os.getenv("STATISTICS_DAYS", 30))
            except ValueError as statistics_days_error:
                raise ImproperlyConfigured("STATISTICS_DAYS must contain the statistics period in days.") from statistics_days_error
            cls._settings["STATISTICS_DAYS"] = timedelta(days=statistics_days)

            cls._settings["STATISTICS_ROLES"] = set(filter(None, os.getenv("STATISTICS_ROLES", "").split(","))) or {"Committee", "Committee-Elect", "Student Rep", "Member", "Guest", "Server Booster", "Foundation Year", "First Year", "Second Year", "Final Year", "Year In Industry", "Year Abroad", "PGT", "PGR", "Alumnus/Alumna", "Postdoc", "Quiz Victor"}

            log_level_choices: Sequence[str] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            console_log_level: str = str(os.getenv("CONSOLE_LOG_LEVEL", "INFO")).upper()
            if console_log_level not in log_level_choices:
                raise ImproperlyConfigured(f"""LOG_LEVEL must be one of {",".join(f'"{log_level_choice}"' for log_level_choice in log_level_choices[:-1])} or \"{log_level_choices[-1]}\".""")
            # noinspection SpellCheckingInspection
            logging.basicConfig(
                level=getattr(logging, console_log_level), format="%(levelname)s | %(module)s: %(message)s"
            )

            cls._is_env_variables_setup = True

    @classmethod
    def setup_django(cls) -> None:
        """
            Setup function to ensure the correct settings module has been loaded
            into the Django process, so that the models (defined using Django)
            can be accessed.
        """

        if not cls._is_django_setup:
            os.environ["DJANGO_SETTINGS_MODULE"] = "db.settings"
            django.setup()

            cls._is_django_setup = True


settings: type[Settings] = Settings
setup_env_variables: Callable[[], None] = Settings.setup_env_variables
setup_django: Callable[[], None] = Settings.setup_django
