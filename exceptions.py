"""Custom exception classes that could be raised within the cogs modules."""

import abc
from collections.abc import Collection
from typing import Any, Final


class ImproperlyConfigured(Exception):
    """Exception class to raise when environment variables are not correctly provided."""


class TeXBotBaseError(BaseException, abc.ABC):
    """Base exception parent class."""

    DEFAULT_MESSAGE: str

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new exception with the given error message."""
        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(self.message)

    def __repr__(self) -> str:
        """Generate a developer-focused representation of the exception's attributes."""
        formatted: str = self.message

        attributes: set[str] = set(self.__dict__.keys())
        attributes.discard("message")
        if attributes:
            formatted += f""" ({", ".join({f"{attribute=}" for attribute in attributes})})"""

        return formatted


class BaseErrorWithErrorCode(TeXBotBaseError, abc.ABC):
    """Base class for exception errors that have an error code."""

    ERROR_CODE: str


class BaseDoesNotExistError(BaseErrorWithErrorCode, ValueError, abc.ABC):
    """Exception class to raise when a required Discord entity is missing."""

    @staticmethod
    def format_does_not_exist_with_dependencies(value: str, does_not_exist_type: str, dependant_commands: Collection[str], dependant_tasks: Collection[str], dependant_events: Collection[str]) -> str:  # noqa: C901, E501, PLR0912
        """Format a string, stating that the given Discord entity does not exist."""
        if not dependant_commands and not dependant_tasks and not dependant_events:
            EMPTY_ARGS_MESSAGE: Final[str] = (
                "The arguments \"dependant_commands\" & \"dependant_tasks\" "
                "cannot all be empty."
            )
            raise ValueError(EMPTY_ARGS_MESSAGE)

        formatted_dependant_commands: str = ""

        if dependant_commands:
            if len(dependant_commands) == 1:
                formatted_dependant_commands += (
                    f"\"/{next(iter(dependant_commands))}\" command"
                )
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

        partial_message: str = (
            f"\"{value}\" {does_not_exist_type} must exist "
            f"in order to use the {formatted_dependant_commands}"
        )

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


class RulesChannelDoesNotExist(TeXBotBaseError, ValueError):
    """Exception class to raise when the channel, marked as the rules channel, is missing."""

    DEFAULT_MESSAGE: str = "There is no channel marked as the rules channel."


class UserNotInCSSDiscordServer(TeXBotBaseError, ValueError):
    """Exception class for when no members of your Discord guild have the given user ID."""

    DEFAULT_MESSAGE: str = (
        "Given user ID does not represent any member of your group's Discord guild."
    )

    def __init__(self, message: str | None = None, user_id: int | None = None) -> None:
        """Initialize a ValueError exception for a non-existent user ID."""
        self.user_id: int | None = user_id

        super().__init__(message)


class EveryoneRoleCouldNotBeRetrieved(BaseErrorWithErrorCode, ValueError):
    """Exception class for when the "@everyone" role could not be retrieved."""

    DEFAULT_MESSAGE: str = (
        "The reference to the \"@everyone\" role could not be correctly retrieved."
    )
    ERROR_CODE: str = "E1042"


class InvalidMessagesJSONFile(TeXBotBaseError, ImproperlyConfigured):
    """Exception class to raise when the messages.json file has an invalid structure."""

    DEFAULT_MESSAGE: str = "The messages JSON file has an invalid structure at the given key."

    def __init__(self, message: str | None = None, dict_key: str | None = None) -> None:
        """Initialize an ImproperlyConfigured exception for an invalid messages.json file."""
        self.dict_key: str | None = dict_key

        super().__init__(message)


class MessagesJSONFileMissingKey(InvalidMessagesJSONFile):
    """Exception class to raise when a key in the messages.json file is missing."""

    DEFAULT_MESSAGE: str = "The messages JSON file is missing a required key."

    def __init__(self, message: str | None = None, missing_key: str | None = None) -> None:
        """Initialize a new InvalidMessagesJSONFile exception for a missing key."""
        super().__init__(message, dict_key=missing_key)


class MessagesJSONFileValueError(InvalidMessagesJSONFile):
    """Exception class to raise when a key in the messages.json file has an invalid value."""

    DEFAULT_MESSAGE: str = "The messages JSON file has an invalid value."

    def __init__(self, message: str | None = None, dict_key: str | None = None, invalid_value: object | None = None) -> None:  # noqa: E501
        """Initialize a new InvalidMessagesJSONFile exception for a key's invalid value."""
        self.invalid_value: object | None = invalid_value

        super().__init__(message, dict_key)


class StrikeTrackingError(TeXBotBaseError, RuntimeError):
    """
    Exception class to raise when any error occurs while tracking moderation actions.

    If this error occurs, it is likely that manually applied moderation actions will be missed
    and not tracked correctly.
    """

    DEFAULT_MESSAGE: str = (
        "An error occurred while trying to track manually applied moderation actions."
    )


class GuildDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord guild is missing."""

    DEFAULT_MESSAGE: str = (
        "Server with given ID does not exist "
        "or is not accessible to the bot."
    )
    ERROR_CODE: str = "E1011"

    def __init__(self, message: str | None = None, guild_id: int | None = None) -> None:
        """Initialize a new DoesNotExist exception for a guild not existing."""
        self.guild_id: int | None = guild_id

        if guild_id and not message:
            message = (
                f"Server with ID \"{self.guild_id}\" does not exist "
                "or is not accessible to the bot."
            )

        super().__init__(message)


class RoleDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord role is missing."""

    DEFAULT_MESSAGE: str = "Role with given name does not exist."

    def __init__(self, message: str | None = None, role_name: str | None = None, dependant_commands: Collection[str] | None = None, dependant_tasks: Collection[str] | None = None, dependant_events: Collection[str] | None = None) -> None:  # noqa: E501
        """Initialize a new DoesNotExist exception for a role not existing."""
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
    """Exception class to raise when the "Committee" Discord role is missing."""

    ERROR_CODE: str = "E1021"

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new RoleDoesNotExist exception with role_name=Committee."""
        # noinspection SpellCheckingInspection
        super().__init__(
            message,
            role_name="Committee",
            dependant_commands={
                "writeroles",
                "editmessage",
                "induct",
                "strike",
                "archive",
                "delete-all",
                "ensure-members-inducted"
            }
        )


class GuestRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Guest" Discord role is missing."""

    ERROR_CODE: str = "E1022"

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new RoleDoesNotExist exception with role_name=Guest."""
        # noinspection SpellCheckingInspection
        super().__init__(
            message,
            role_name="Guest",
            dependant_commands={"induct", "stats", "archive", "ensure-members-inducted"},
            dependant_tasks={
                "kick_no_introduction_discord_members",
                "introduction_reminder",
                "get_roles_reminder"
            }
        )


class MemberRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Member" Discord role is missing."""

    ERROR_CODE: str = "E1023"

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new RoleDoesNotExist exception with role_name=Member."""
        # noinspection SpellCheckingInspection
        super().__init__(
            message,
            role_name="Member",
            dependant_commands={"makemember", "ensure-members-inducted"}
        )


class ArchivistRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Archivist" Discord role is missing."""

    ERROR_CODE: str = "E1024"

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new RoleDoesNotExist exception with role_name=Archivist."""
        super().__init__(message, role_name="Archivist", dependant_commands={"archive"})


class ChannelDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord channel is missing."""

    DEFAULT_MESSAGE: str = "Channel with given name does not exist."

    def __init__(self, message: str | None = None, channel_name: str | None = None, dependant_commands: Collection[str] | None = None, dependant_tasks: Collection[str] | None = None, dependant_events: Collection[str] | None = None) -> None:  # noqa: E501
        """Initialize a new DoesNotExist exception for a channel not existing."""
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
    """Exception class to raise when the "Roles" Discord channel is missing."""

    ERROR_CODE: str = "E1031"

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new ChannelDoesNotExist exception with channel_name=roles."""
        # noinspection SpellCheckingInspection
        super().__init__(message, channel_name="roles", dependant_commands={"writeroles"})


class GeneralChannelDoesNotExist(ChannelDoesNotExist):
    """Exception class to raise when the "General" Discord channel is missing."""

    ERROR_CODE: str = "E1032"

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new ChannelDoesNotExist exception with channel_name=general."""
        # noinspection SpellCheckingInspection
        super().__init__(message, channel_name="general", dependant_commands={"induct"})
