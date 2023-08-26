"""
    Custom exception classes that could be raised within the cogs modules.
"""

import abc
from typing import Any, Collection


class ImproperlyConfigured(Exception):
    """
        Exception class to raise when environment variables are not correctly
        supplied.
    """

    pass


class BaseError(BaseException, abc.ABC):
    """
        Base exception mixin that provides the functionality for custom
        exceptions to inherit from, along with an existing concrete type.
    """

    DEFAULT_MESSAGE: str

    def __init__(self, message: str | None = None) -> None:
        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(self.message)

    def __repr__(self) -> str:
        formatted: str = self.message

        attributes: set[str] = set(self.__dict__.keys())
        attributes.discard("message")
        if attributes:
            formatted += f""" ({", ".join({f"{attribute=}" for attribute in attributes})})"""

        return formatted


class BaseDoesNotExistError(ValueError, BaseError, abc.ABC):
    """
        Exception class to raise when a required Discord entity with the given
        type and name/ID does not exist.
    """

    @staticmethod
    def format_does_not_exist_with_dependencies(value: str, does_not_exist_type: str, dependant_commands: Collection[str], dependant_tasks: Collection[str], dependant_events: Collection[str]) -> str:
        """
            Returns a formatted string of an error that the given Discord
            entity does not exist.
        """

        if not dependant_commands and not dependant_tasks and not dependant_events:
            raise ValueError("The arguments \"dependant_commands\" & \"dependant_tasks\" cannot all be empty.")

        formatted_dependant_commands: str = ""

        if dependant_commands:
            if len(dependant_commands) == 1:
                formatted_dependant_commands += f"\"/{next(iter(dependant_commands))}\" command"
            else:
                index: int
                dependant_command: str
                for index, dependant_command in enumerate(dependant_commands):
                    formatted_dependant_commands += f"\"/{dependant_command}\""

                    if index < len(dependant_commands) - 2:
                        formatted_dependant_commands += ", "
                    elif index == len(dependant_commands) - 2:
                        formatted_dependant_commands += " & "

                formatted_dependant_commands += " commands"

        if does_not_exist_type == "channel":
            value = f"#{value}"

        partial_message: str = f"""\"{value}\" {does_not_exist_type} must exist in order to use the {formatted_dependant_commands}"""

        if dependant_tasks:
            formatted_dependant_tasks: str = ""

            if dependant_commands:
                if not dependant_events:
                    partial_message += " and the "
                else:
                    partial_message += ", the "

            if len(dependant_tasks) == 1:
                formatted_dependant_tasks += f"\"{next(iter(dependant_tasks))}\" task"
            else:
                dependant_task: str
                for index, dependant_task in enumerate(dependant_tasks):
                    formatted_dependant_tasks += f"\"{dependant_task}\""

                    if index < len(dependant_tasks) - 2:
                        formatted_dependant_tasks += ", "
                    elif index == len(dependant_tasks) - 2:
                        formatted_dependant_tasks += " & "

                formatted_dependant_tasks += " tasks"

            partial_message += formatted_dependant_tasks

        if dependant_events:
            formatted_dependant_events: str = ""

            if dependant_commands or dependant_tasks:
                partial_message += " and the "

            if len(dependant_events) == 1:
                formatted_dependant_events += f"\"{next(iter(dependant_events))}\" event"
            else:
                dependant_event: str
                for index, dependant_event in enumerate(dependant_events):
                    formatted_dependant_events += f"\"{dependant_event}\""

                    if index < len(dependant_events) - 2:
                        formatted_dependant_events += ", "
                    elif index == len(dependant_events) - 2:
                        formatted_dependant_events += " & "

                formatted_dependant_events += " events"

            partial_message += formatted_dependant_events

        return f"{partial_message}."


class InvalidMessagesJSONFile(ImproperlyConfigured, BaseError):
    """
        Exception class to raise when the provided messages.json file has an
        invalid structure, at the given key, in some way.
    """

    DEFAULT_MESSAGE: str = "The messages JSON file has an invalid structure at the given key."

    def __init__(self, message: str | None = None, dict_key: str | None = None) -> None:
        self.dict_key: str | None = dict_key

        super().__init__(message)


class MessagesJSONFileMissingKey(InvalidMessagesJSONFile):
    """
        Exception class to raise when the provided messages.json file is missing
        a required key.
    """

    DEFAULT_MESSAGE: str = "The messages JSON file is missing a required key."

    def __init__(self, message: str | None = None, missing_key: str | None = None) -> None:
        super().__init__(message, dict_key=missing_key)


class MessagesJSONFileValueError(InvalidMessagesJSONFile):
    """
        Exception class to raise when the provided messages.json file has an
        invalid value for the given key.
    """

    DEFAULT_MESSAGE: str = "The messages JSON file has an invalid value."

    def __init__(self, message: str | None = None, dict_key: str | None = None, invalid_value: Any | None = None) -> None:
        self.invalid_value: Any | None = invalid_value

        super().__init__(message, dict_key)


class GuildDoesNotExist(BaseDoesNotExistError):
    """
        Exception class to raise when a required Discord guild with the given
        ID does not exist.
    """

    DEFAULT_MESSAGE: str = "Server with given ID does not exist or is not accessible to the bot."

    def __init__(self, message: str | None = None, guild_id: int | None = None) -> None:
        self.guild_id: int | None = guild_id

        if guild_id and not message:
            message = f"Server with ID \"{self.guild_id}\" does not exist or is not accessible to the bot."

        super().__init__(message)


class RoleDoesNotExist(BaseDoesNotExistError):
    """
        Exception class to raise when a required Discord role with the given
        name does not exist.
    """

    DEFAULT_MESSAGE: str = "Role with given name does not exist."

    def __init__(self, message: str | None = None, role_name: str | None = None, dependant_commands: Collection[str] | None = None, dependant_tasks: Collection[str] | None = None, dependant_events: Collection[str] | None = None) -> None:
        self.role_name: str | None = role_name

        self.dependant_commands: set[str] = set()
        if dependant_commands:
            self.dependant_commands = set(dependant_commands)

        self.dependant_tasks: set[str] = set()
        if dependant_tasks:
            self.dependant_tasks = set(dependant_tasks)

        self.dependant_events: set[str] = set()
        if dependant_events:
            self.dependant_events = set(dependant_events)

        if self.role_name and not message:
            if self.dependant_commands or self.dependant_tasks or self.dependant_events:
                message = self.format_does_not_exist_with_dependencies(
                    self.role_name,
                    "role",
                    self.dependant_commands,
                    self.dependant_tasks,
                    self.dependant_events
                )
            else:
                message = f"Role with name \"{self.role_name}\" does not exist."

        super().__init__(message)


class CommitteeRoleDoesNotExist(RoleDoesNotExist):
    """
        Exception class to raise when the required Discord role with the name
        "Committee" does not exist.
    """

    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, role_name="Committee", dependant_commands={"writeroles", "editmessage", "induct", "archive", "delete-all"})


class GuestRoleDoesNotExist(RoleDoesNotExist):
    """
        Exception class to raise when the required Discord role with the name
        "Guest" does not exist.
    """

    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, role_name="Guest", dependant_commands={"induct", "makemember", "stats", "archive"}, dependant_tasks={"kick_no_introduction_members", "introduction_reminder"})


class MemberRoleDoesNotExist(RoleDoesNotExist):
    """
        Exception class to raise when the required Discord role with the name
        "Member" does not exist.
    """

    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, role_name="Member", dependant_commands={"makemember"})


class ArchivistRoleDoesNotExist(RoleDoesNotExist):
    """
        Exception class to raise when the required Discord role with the name
        "Archivist" does not exist.
    """

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message, role_name="Archivist", dependant_commands={"archive"})


class ChannelDoesNotExist(BaseDoesNotExistError):
    """
        Exception class to raise when a required Discord channel with the given
        name does not exist.
    """

    DEFAULT_MESSAGE: str = "Channel with given name does not exist."

    def __init__(self, message: str | None = None, channel_name: str | None = None, dependant_commands: Collection[str] | None = None, dependant_tasks: Collection[str] | None = None, dependant_events: Collection[str] | None = None) -> None:
        self.channel_name: str | None = channel_name

        self.dependant_commands: set[str] = set()
        if dependant_commands:
            self.dependant_commands = set(dependant_commands)

        self.dependant_tasks: set[str] = set()
        if dependant_tasks:
            self.dependant_tasks = set(dependant_tasks)

        self.dependant_events: set[str] = set()
        if dependant_events:
            self.dependant_events = set(dependant_events)

        if self.channel_name and not message:
            if self.dependant_commands or self.dependant_tasks or self.dependant_events:
                message = self.format_does_not_exist_with_dependencies(
                    self.channel_name,
                    "channel",
                    self.dependant_commands,
                    self.dependant_tasks,
                    self.dependant_events
                )
            else:
                message = f"Channel with name \"{self.channel_name}\" does not exist."

        super().__init__(message)


class RolesChannelDoesNotExist(ChannelDoesNotExist):
    """
        Exception class to raise when a required Discord channel with the name
        "Roles" does not exist.
    """

    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, channel_name="roles", dependant_commands={"writeroles"})


class GeneralChannelDoesNotExist(ChannelDoesNotExist):
    """
        Exception class to raise when a required Discord channel with the name
        "General" does not exist.
    """

    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, channel_name="general", dependant_commands={"induct"})
