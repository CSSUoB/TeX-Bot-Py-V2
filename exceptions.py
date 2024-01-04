"""Custom exception classes that could be raised within the cogs modules."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "ImproperlyConfigured",
    "TeXBotBaseError",
    "BaseErrorWithErrorCode",
    "BaseDoesNotExistError",
    "RulesChannelDoesNotExist",
    "DiscordMemberNotInMainGuild",
    "EveryoneRoleCouldNotBeRetrieved",
    "InvalidMessagesJSONFile",
    "MessagesJSONFileMissingKey",
    "MessagesJSONFileValueError",
    "StrikeTrackingError",
    "GuildDoesNotExist",
    "RoleDoesNotExist",
    "CommitteeRoleDoesNotExist",
    "GuestRoleDoesNotExist",
    "MemberRoleDoesNotExist",
    "ArchivistRoleDoesNotExist",
    "ChannelDoesNotExist",
    "RolesChannelDoesNotExist",
    "GeneralChannelDoesNotExist"
)

import abc
from collections.abc import Collection
from typing import Final

from classproperties import classproperty


class ImproperlyConfigured(Exception):
    """Exception class to raise when environment variables are not correctly provided."""


class TeXBotBaseError(BaseException, abc.ABC):
    """Base exception parent class."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401

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

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401


class BaseDoesNotExistError(BaseErrorWithErrorCode, ValueError, abc.ABC):
    """Exception class to raise when a required Discord entity is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean that all bot commands require this Discord entity,
        or no bot commands require this Discord entity.
        """  # noqa: D401
        return frozenset()

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_TASKS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot tasks that require this Discord entity.

        This set being empty could mean that all bot tasks require this Discord entity,
        or no bot tasks require this Discord entity.
        """  # noqa: D401
        return frozenset()

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_EVENTS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot events that require this Discord entity.

        This set being empty could mean that all bot events require this Discord entity,
        or no bot events require this Discord entity.
        """  # noqa: D401
        return frozenset()

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def DOES_NOT_EXIST_TYPE(cls) -> str:  # noqa: N802,N805
        """The name of the Discord entity that this `DoesNotExistError` is associated with."""  # noqa: D401

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

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "There is no channel marked as the rules channel."


class DiscordMemberNotInMainGuild(TeXBotBaseError, ValueError):
    """Exception class for when no members of your Discord guild have the given user ID."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "Given user ID does not represent any member of your group's Discord guild."

    def __init__(self, message: str | None = None, user_id: int | None = None) -> None:
        """Initialize a ValueError exception for a non-existent user ID."""
        self.user_id: int | None = user_id

        super().__init__(message)


class EveryoneRoleCouldNotBeRetrieved(BaseErrorWithErrorCode, ValueError):
    """Exception class for when the "@everyone" role could not be retrieved."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "The reference to the \"@everyone\" role could not be correctly retrieved."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1042"


class InvalidMessagesJSONFile(TeXBotBaseError, ImproperlyConfigured):
    """Exception class to raise when the messages.json file has an invalid structure."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "The messages JSON file has an invalid structure at the given key."

    def __init__(self, message: str | None = None, dict_key: str | None = None) -> None:
        """Initialize an ImproperlyConfigured exception for an invalid messages.json file."""
        self.dict_key: str | None = dict_key

        super().__init__(message)


class MessagesJSONFileMissingKey(InvalidMessagesJSONFile):
    """Exception class to raise when a key in the messages.json file is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "The messages JSON file is missing a required key."

    def __init__(self, message: str | None = None, missing_key: str | None = None) -> None:
        """Initialize a new InvalidMessagesJSONFile exception for a missing key."""
        super().__init__(message, dict_key=missing_key)


class MessagesJSONFileValueError(InvalidMessagesJSONFile):
    """Exception class to raise when a key in the messages.json file has an invalid value."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "The messages JSON file has an invalid value."

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

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "An error occurred while trying to track manually applied moderation actions."


class GuildDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord guild is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "Server with given ID does not exist or is not accessible to the bot."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1011"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DOES_NOT_EXIST_TYPE(cls) -> str:  # noqa: N802,N805
        """The name of the Discord entity that this `DoesNotExistError` is associated with."""  # noqa: D401
        return "guild"

    def __init__(self, message: str | None = None, guild_id: int | None = None) -> None:
        """Initialize a new DoesNotExist exception for a guild not existing."""
        self.guild_id: int | None = guild_id

        if guild_id and not message:
            message = self.DEFAULT_MESSAGE.replace("given ID", f"ID \"{self.guild_id}\"")

        super().__init__(message)


class RoleDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return f"Role with name \"{cls.ROLE_NAME}\" does not exist."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DOES_NOT_EXIST_TYPE(cls) -> str:  # noqa: N802,N805
        """The name of the Discord entity that this `DoesNotExistError` is associated with."""  # noqa: D401
        return "role"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new DoesNotExist exception for a role not existing."""
        HAS_DEPENDANTS: Final[bool] = bool(
            self.DEPENDENT_COMMANDS or self.DEPENDENT_TASKS or self.DEPENDENT_EVENTS
        )

        if not message and HAS_DEPENDANTS:
            message = self.format_does_not_exist_with_dependencies(
                value=self.ROLE_NAME,
                does_not_exist_type="role",
                dependant_commands=self.DEPENDENT_COMMANDS,
                dependant_tasks=self.DEPENDENT_TASKS,
                dependant_events=self.DEPENDENT_EVENTS
            )

        super().__init__(message)


class CommitteeRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Committee" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1021"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean that all bot commands require this Discord entity,
        or no bot commands require this Discord entity.
        """  # noqa: D401
        # noinspection SpellCheckingInspection
        return frozenset(
            {
                "writeroles",
                "editmessage",
                "induct",
                "strike",
                "archive",
                "delete-all",
                "ensure-members-inducted"
            }
        )

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Committee"


class GuestRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Guest" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1022"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean that all bot commands require this Discord entity,
        or no bot commands require this Discord entity.
        """  # noqa: D401
        # noinspection SpellCheckingInspection
        return frozenset({"induct", "stats", "archive", "ensure-members-inducted"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_TASKS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot tasks that require this Discord entity.

        This set being empty could mean that all bot tasks require this Discord entity,
        or no bot tasks require this Discord entity.
        """  # noqa: D401
        # noinspection SpellCheckingInspection
        return frozenset(
            {
                "kick_no_introduction_discord_members",
                "introduction_reminder",
                "get_roles_reminder"
            }
        )

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Guest"


class MemberRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Member" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1023"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean that all bot commands require this Discord entity,
        or no bot commands require this Discord entity.
        """  # noqa: D401
        # noinspection SpellCheckingInspection
        return frozenset({"makemember", "ensure-members-inducted"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Member"


class ArchivistRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Archivist" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1024"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean that all bot commands require this Discord entity,
        or no bot commands require this Discord entity.
        """  # noqa: D401
        # noinspection SpellCheckingInspection
        return frozenset({"archive"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Archivist"


class ChannelDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord channel is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return f"Channel with name \"{cls.CHANNEL_NAME}\" does not exist."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DOES_NOT_EXIST_TYPE(cls) -> str:  # noqa: N802,N805
        """The name of the Discord entity that this `DoesNotExistError` is associated with."""  # noqa: D401
        return "channel"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def CHANNEL_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord channel that does not exist."""  # noqa: D401

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new DoesNotExist exception for a role not existing."""
        HAS_DEPENDANTS: Final[bool] = bool(
            self.DEPENDENT_COMMANDS or self.DEPENDENT_TASKS or self.DEPENDENT_EVENTS
        )

        if not message and HAS_DEPENDANTS:
            message = self.format_does_not_exist_with_dependencies(
                value=self.CHANNEL_NAME,
                does_not_exist_type="channel",
                dependant_commands=self.DEPENDENT_COMMANDS,
                dependant_tasks=self.DEPENDENT_TASKS,
                dependant_events=self.DEPENDENT_EVENTS
            )

        super().__init__(message)


class RolesChannelDoesNotExist(ChannelDoesNotExist):
    """Exception class to raise when the "Roles" Discord channel is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1031"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean that all bot commands require this Discord entity,
        or no bot commands require this Discord entity.
        """  # noqa: D401
        # noinspection SpellCheckingInspection
        return frozenset({"writeroles"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def CHANNEL_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord channel that does not exist."""  # noqa: D401
        return "roles"


class GeneralChannelDoesNotExist(ChannelDoesNotExist):
    """Exception class to raise when the "General" Discord channel is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1032"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean that all bot commands require this Discord entity,
        or no bot commands require this Discord entity.
        """  # noqa: D401
        # noinspection SpellCheckingInspection
        return frozenset({"induct"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def CHANNEL_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord channel that does not exist."""  # noqa: D401
        return "general"
