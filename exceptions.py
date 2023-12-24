"""Custom exception classes that could be raised within the cogs modules."""

import abc
from typing import Any, Final

from classproperties import classproperty


class ImproperlyConfiguredError(Exception):
    """Exception class to raise when environment variables are not correctly provided."""


class BaseTeXBotError(BaseException, abc.ABC):
    """Base exception parent class."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""

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


class BaseErrorWithErrorCode(BaseTeXBotError, abc.ABC):
    """Base class for exception errors that have an error code."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        """"""


class BaseDoesNotExistError(BaseErrorWithErrorCode, ValueError, abc.ABC):
    """Exception class to raise when a required Discord entity is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
        return frozenset()  # TODO: mention empty meaning all/none in docstring

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_TASKS(self) -> frozenset[str]:  # noqa: N805,N802
        return frozenset()  # TODO: mention empty meaning all/none in docstring

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_EVENTS(self) -> frozenset[str]:  # noqa: N805,N802
        return frozenset()  # TODO: mention empty meaning all/none in docstring

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def DOES_NOT_EXIST_TYPE(self) -> str:  # noqa: N805,N802
        """"""

    @classmethod
    def get_formatted_message(cls, non_existent_object_identifier: str) -> str:  # noqa: C901, E501, PLR0912
        """
        Format the exception message with the dependants that require the non-existent object.

        The message will also state that the given Discord entity does not exist.
        """
        if not cls.DEPENDANT_COMMANDS and not cls.DEPENDANT_TASKS and not cls.DEPENDANT_EVENTS:
            NO_DEPENDANTS_MESSAGE: Final[str] = (
                "Cannot get formatted message when non-existent object has no dependants."
            )
            raise ValueError(NO_DEPENDANTS_MESSAGE)

        formatted_dependant_commands: str = ""

        if cls.DEPENDANT_COMMANDS:
            if len(cls.DEPENDANT_COMMANDS) == 1:
                formatted_dependant_commands += (
                    f"\"/{next(cls.DEPENDANT_COMMANDS)}\" command"
                )
            else:
                index: int
                dependant_command: str
                for index, dependant_command in enumerate(cls.DEPENDANT_COMMANDS):
                    formatted_dependant_commands += f"\"/{dependant_command}\""

                    if index < len(cls.DEPENDANT_COMMANDS) - 2:
                        formatted_dependant_commands += ", "
                    elif index == len(cls.DEPENDANT_COMMANDS) - 2:
                        formatted_dependant_commands += " & "

                formatted_dependant_commands += " commands"

        if cls.DOES_NOT_EXIST_TYPE.strip().lower() == "channel":
            non_existent_object_identifier = f"#{non_existent_object_identifier}"

        partial_message: str = (
            f"\"{non_existent_object_identifier}\" {cls.DOES_NOT_EXIST_TYPE} must exist "
            f"in order to use the {formatted_dependant_commands}"
        )

        if cls.DEPENDANT_TASKS:
            formatted_dependant_tasks: str = ""

            if cls.DEPENDANT_COMMANDS:
                if not cls.DEPENDANT_EVENTS:
                    partial_message += " and the "
                else:
                    partial_message += ", the "

            if len(cls.DEPENDANT_TASKS) == 1:
                formatted_dependant_tasks += f"\"{next(cls.DEPENDANT_TASKS)}\" task"
            else:
                dependant_task: str
                for index, dependant_task in enumerate(cls.DEPENDANT_TASKS):
                    formatted_dependant_tasks += f"\"{dependant_task}\""

                    if index < len(cls.DEPENDANT_TASKS) - 2:
                        formatted_dependant_tasks += ", "
                    elif index == len(cls.DEPENDANT_TASKS) - 2:
                        formatted_dependant_tasks += " & "

                formatted_dependant_tasks += " tasks"

            partial_message += formatted_dependant_tasks

        if cls.DEPENDANT_EVENTS:
            formatted_dependant_events: str = ""

            if cls.DEPENDANT_COMMANDS or cls.DEPENDANT_TASKS:
                partial_message += " and the "

            if len(cls.DEPENDANT_EVENTS) == 1:
                formatted_dependant_events += f"\"{next(iter(cls.DEPENDANT_EVENTS))}\" event"
            else:
                dependant_event: str
                for index, dependant_event in enumerate(cls.DEPENDANT_EVENTS):
                    formatted_dependant_events += f"\"{dependant_event}\""

                    if index < len(cls.DEPENDANT_EVENTS) - 2:
                        formatted_dependant_events += ", "
                    elif index == len(cls.DEPENDANT_EVENTS) - 2:
                        formatted_dependant_events += " & "

                formatted_dependant_events += " events"

            partial_message += formatted_dependant_events

        return f"{partial_message}."


class RulesChannelDoesNotExist(BaseTeXBotError, ValueError):
    """Exception class to raise when the channel, marked as the rules channel, is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""
        return "There is no channel marked as the rules channel."


class UserNotInCSSDiscordServer(BaseTeXBotError, ValueError):
    """Exception class for when no members of the CSS Discord Server have the given user ID."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""
        return "Given user ID does not represent any member of the CSS Discord Server."

    def __init__(self, message: str | None = None, user_id: int | None = None) -> None:
        """Initialize a ValueError exception for a non-existent user ID."""
        self.user_id: int | None = user_id

        super().__init__(message)


class EveryoneRoleCouldNotBeRetrieved(BaseErrorWithErrorCode, ValueError):
    """Exception class for when the "@everyone" role could not be retrieved."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""
        return "The reference to the \"@everyone\" role could not be correctly retrieved."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        """"""
        return "E1042"


class InvalidMessagesJSONFile(BaseTeXBotError, ImproperlyConfiguredError):
    """Exception class to raise when the messages.json file has an invalid structure."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""
        return "The messages JSON file has an invalid structure at the given key."

    def __init__(self, message: str | None = None, dict_key: str | None = None) -> None:
        """Initialize an ImproperlyConfigured exception for an invalid messages.json file."""
        self.dict_key: str | None = dict_key

        super().__init__(message)


class MessagesJSONFileMissingKey(InvalidMessagesJSONFile):
    """Exception class to raise when a key in the messages.json file is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""
        return "The messages JSON file is missing a required key."

    def __init__(self, message: str | None = None, missing_key: str | None = None) -> None:
        """Initialize a new InvalidMessagesJSONFile exception for a missing key."""
        super().__init__(message, dict_key=missing_key)


class MessagesJSONFileValueError(InvalidMessagesJSONFile):
    """Exception class to raise when a key in the messages.json file has an invalid value."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""
        return "The messages JSON file has an invalid value."

    def __init__(self, message: str | None = None, dict_key: str | None = None, invalid_value: Any | None = None) -> None:  # noqa: E501
        """Initialize a new InvalidMessagesJSONFile exception for a key's invalid value."""
        self.invalid_value: Any | None = invalid_value

        super().__init__(message, dict_key)


class StrikeTrackingError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when any error occurs while tracking moderation actions.

    If this error occurs, it is likely that manually applied moderation actions will be missed
    and not tracked correctly.
    """

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        """"""
        return "An error occurred while trying to track manually applied moderation actions."


class GuildDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord guild is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        return "Server with given ID does not exist or is not accessible to the bot."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        return "E1011"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DOES_NOT_EXIST_TYPE(self) -> str:  # noqa: N805,N802
        return "guild"

    def __init__(self, message: str | None = None, guild_id: int | None = None) -> None:
        """Initialize a new DoesNotExist exception for a guild not existing."""
        self.guild_id: int | None = guild_id

        if guild_id and not message:
            message = (
                f"Server with ID \"{self.guild_id}\" does not exist "
                "or is not accessible to the bot."
            )

        super().__init__(message)


class RoleDoesNotExist(BaseDoesNotExistError, abc.ABC):
    """Exception class to raise when a required Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        return f"Role with name \"{self.ROLE_NAME}\" does not exist."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DOES_NOT_EXIST_TYPE(self) -> str:  # noqa: N805,N802
        return "role"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def ROLE_NAME(self) -> str:  # noqa: N805,N802
        """"""

    def __init__(self, message: str | None = None) -> None:  # noqa: E501
        """Initialize a new DoesNotExist exception for a role not existing."""
        if not message and (self.DEPENDANT_COMMANDS or self.DEPENDANT_TASKS or self.DEPENDANT_EVENTS):
            message = self.get_formatted_message(non_existent_object_identifier=self.ROLE_NAME)

        super().__init__(message)


class CommitteeRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Committee" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        return "E1021"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
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
    def ROLE_NAME(self) -> str:  # noqa: N805,N802
        return "Committee"


class GuestRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Guest" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        return "E1022"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
        # noinspection SpellCheckingInspection
        return frozenset({"induct", "stats", "archive", "ensure-members-inducted"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_TASKS(self) -> frozenset[str]:  # noqa: N805,N802
        # noinspection SpellCheckingInspection
        return frozenset(
            {
                "kick_no_introduction_members",
                "introduction_reminder",
                "get_roles_reminder"
            }
        )

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(self) -> str:  # noqa: N805,N802
        return "Guest"


class MemberRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Member" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        return "E1023"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
        # noinspection SpellCheckingInspection
        return frozenset({"makemember", "ensure-members-inducted"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(self) -> str:  # noqa: N805,N802
        return "Member"


class ArchivistRoleDoesNotExist(RoleDoesNotExist):
    """Exception class to raise when the "Archivist" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        return "E1024"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
        # noinspection SpellCheckingInspection
        return frozenset({"archive"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(self) -> str:  # noqa: N805,N802
        return "Archivist"


class ChannelDoesNotExist(BaseDoesNotExistError):
    """Exception class to raise when a required Discord channel is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
        return f"Channel with name \"{self.CHANNEL_NAME}\" does not exist."

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DOES_NOT_EXIST_TYPE(self) -> str:  # noqa: N805,N802
        return "channel"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def CHANNEL_NAME(self) -> str:  # noqa: N805,N802
        """"""

    def __init__(self, message: str | None = None) -> None:  # noqa: E501
        """Initialize a new DoesNotExist exception for a role not existing."""
        if not message and (self.DEPENDANT_COMMANDS or self.DEPENDANT_TASKS or self.DEPENDANT_EVENTS):
            message = self.get_formatted_message(
                non_existent_object_identifier=self.CHANNEL_NAME
            )

        super().__init__(message)


class RolesChannelDoesNotExist(ChannelDoesNotExist):
    """Exception class to raise when the "Roles" Discord channel is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        return "E1031"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
        # noinspection SpellCheckingInspection
        return frozenset({"writeroles"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def CHANNEL_NAME(self) -> str:  # noqa: N805,N802
        return "roles"


class GeneralChannelDoesNotExist(ChannelDoesNotExist):
    """Exception class to raise when the "General" Discord channel is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(self) -> str:  # noqa: N805,N802
        return "E1032"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
        # noinspection SpellCheckingInspection
        return frozenset({"induct"})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def CHANNEL_NAME(self) -> str:  # noqa: N805,N802
        return "general"
