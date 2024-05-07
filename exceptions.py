"""Custom exception classes that could be raised within the cogs modules."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "ImproperlyConfiguredError",
    "BaseTeXBotError",
    "BaseErrorWithErrorCode",
    "BaseDoesNotExistError",
    "RulesChannelDoesNotExistError",
    "DiscordMemberNotInMainGuildError",
    "EveryoneRoleCouldNotBeRetrievedError",
    "InvalidMessagesJSONFileError",
    "MessagesJSONFileMissingKeyError",
    "MessagesJSONFileValueError",
    "StrikeTrackingError",
    "NoAuditLogsStrikeTrackingError",
    "GuildDoesNotExistError",
    "RoleDoesNotExistError",
    "CommitteeRoleDoesNotExistError",
    "GuestRoleDoesNotExistError",
    "MemberRoleDoesNotExistError",
    "ArchivistRoleDoesNotExistError",
    "ChannelDoesNotExistError",
    "RolesChannelDoesNotExistError",
    "GeneralChannelDoesNotExistError",
)


import abc
from typing import Final

from classproperties import classproperty


class ImproperlyConfiguredError(Exception):
    """Exception class to raise when environment variables are not correctly provided."""


class BaseTeXBotError(BaseException, abc.ABC):
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

        attributes: dict[str, object] = self.__dict__
        attributes.pop("message")
        if attributes:
            formatted += f""" ({
                ", ".join(
                    {
                        f"{attribute_name}={attribute_value!r}"
                        for attribute_name, attribute_value
                        in attributes.items()
                    }
                )
            })"""

        return formatted


class BaseErrorWithErrorCode(BaseTeXBotError, abc.ABC):
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

    @classmethod
    def get_formatted_message(cls, non_existent_object_identifier: str) -> str:  # noqa: C901, PLR0912, PLR0915
        """
        Format the exception message with the dependants that require the non-existent object.

        The message will also state that the given Discord entity does not exist.
        """
        if not cls.DEPENDENT_COMMANDS and not cls.DEPENDENT_TASKS and not cls.DEPENDENT_EVENTS:
            NO_DEPENDANTS_MESSAGE: Final[str] = (
                "Cannot get formatted message when non-existent object has no dependants."
            )
            raise ValueError(NO_DEPENDANTS_MESSAGE)

        formatted_dependent_commands: str = ""

        if cls.DEPENDENT_COMMANDS:
            if len(cls.DEPENDENT_COMMANDS) == 1:
                formatted_dependent_commands += (
                    f"\"/{next(iter(cls.DEPENDENT_COMMANDS))}\" command"
                )
            else:
                index: int
                dependent_command: str
                for index, dependent_command in enumerate(cls.DEPENDENT_COMMANDS):
                    formatted_dependent_commands += f"\"/{dependent_command}\""

                    if index < len(cls.DEPENDENT_COMMANDS) - 2:
                        formatted_dependent_commands += ", "
                    elif index == len(cls.DEPENDENT_COMMANDS) - 2:
                        formatted_dependent_commands += " & "

                formatted_dependent_commands += " commands"

        if cls.DOES_NOT_EXIST_TYPE.strip().lower() == "channel":
            non_existent_object_identifier = f"#{non_existent_object_identifier}"

        partial_message: str = (
            f"\"{non_existent_object_identifier}\" {cls.DOES_NOT_EXIST_TYPE} must exist "
            f"in order to use the {formatted_dependent_commands}"
        )

        if cls.DEPENDENT_TASKS:
            formatted_dependent_tasks: str = ""

            if cls.DEPENDENT_COMMANDS:
                if not cls.DEPENDENT_EVENTS:
                    partial_message += " and the "
                else:
                    partial_message += ", the "

            if len(cls.DEPENDENT_TASKS) == 1:
                formatted_dependent_tasks += f"\"{next(iter(cls.DEPENDENT_TASKS))}\" task"
            else:
                dependent_task: str
                for index, dependent_task in enumerate(cls.DEPENDENT_TASKS):
                    formatted_dependent_tasks += f"\"{dependent_task}\""

                    if index < len(cls.DEPENDENT_TASKS) - 2:
                        formatted_dependent_tasks += ", "
                    elif index == len(cls.DEPENDENT_TASKS) - 2:
                        formatted_dependent_tasks += " & "

                formatted_dependent_tasks += " tasks"

            partial_message += formatted_dependent_tasks

        if cls.DEPENDENT_EVENTS:
            formatted_dependent_events: str = ""

            if cls.DEPENDENT_COMMANDS or cls.DEPENDENT_TASKS:
                partial_message += " and the "

            if len(cls.DEPENDENT_EVENTS) == 1:
                formatted_dependent_events += f"\"{next(iter(cls.DEPENDENT_EVENTS))}\" event"
            else:
                dependent_event: str
                for index, dependent_event in enumerate(cls.DEPENDENT_EVENTS):
                    formatted_dependent_events += f"\"{dependent_event}\""

                    if index < len(cls.DEPENDENT_EVENTS) - 2:
                        formatted_dependent_events += ", "
                    elif index == len(cls.DEPENDENT_EVENTS) - 2:
                        formatted_dependent_events += " & "

                formatted_dependent_events += " events"

            partial_message += formatted_dependent_events

        return f"{partial_message}."


class RulesChannelDoesNotExistError(BaseTeXBotError, ValueError):
    """Exception class to raise when the channel, marked as the rules channel, is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "There is no channel marked as the rules channel."


class DiscordMemberNotInMainGuildError(BaseTeXBotError, ValueError):
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


class EveryoneRoleCouldNotBeRetrievedError(BaseErrorWithErrorCode, ValueError):
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


class InvalidMessagesJSONFileError(BaseTeXBotError, ImproperlyConfiguredError):
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


class MessagesJSONFileMissingKeyError(InvalidMessagesJSONFileError):
    """Exception class to raise when a key in the messages.json file is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "The messages JSON file is missing a required key."

    def __init__(self, message: str | None = None, missing_key: str | None = None) -> None:
        """Initialize a new InvalidMessagesJSONFile exception for a missing key."""
        super().__init__(message, dict_key=missing_key)

    @property
    def missing_key(self) -> str | None:
        """The key that was missing from the messages.json file."""
        return self.dict_key

    @missing_key.setter
    def missing_key(self, value: str | None) -> None:
        self.dict_key = value


class MessagesJSONFileValueError(InvalidMessagesJSONFileError):
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


class StrikeTrackingError(BaseTeXBotError, RuntimeError):
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


class NoAuditLogsStrikeTrackingError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when there are no audit logs to resolve the committee member.

    If this error occurs, it is likely that manually applied moderation actions will be missed
    and not tracked correctly.
    """

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "Unable to retrieve audit log entry after possible manual moderation action."


class GuildDoesNotExistError(BaseDoesNotExistError):
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


class RoleDoesNotExistError(BaseDoesNotExistError, abc.ABC):
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
            self.DEPENDENT_COMMANDS or self.DEPENDENT_TASKS or self.DEPENDENT_EVENTS,
        )

        if not message and HAS_DEPENDANTS:
            message = self.get_formatted_message(non_existent_object_identifier=self.ROLE_NAME)

        super().__init__(message)


class CommitteeRoleDoesNotExistError(RoleDoesNotExistError):
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
                "ensure-members-inducted",
            },
        )

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Committee"


class GuestRoleDoesNotExistError(RoleDoesNotExistError):
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
                "get_roles_reminder",
            },
        )

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Guest"


class MemberRoleDoesNotExistError(RoleDoesNotExistError):
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


class ArchivistRoleDoesNotExistError(RoleDoesNotExistError):
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

class ApplicantRoleDoesNotExistError(RoleDoesNotExistError):
    """Exception class to raise when the "Applicant" Discord role is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
        return "E1025"

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def ROLE_NAME(cls) -> str:  # noqa: N802,N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Archivist"


class ChannelDoesNotExistError(BaseDoesNotExistError):
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
            self.DEPENDENT_COMMANDS or self.DEPENDENT_TASKS or self.DEPENDENT_EVENTS,
        )

        if not message and HAS_DEPENDANTS:
            message = self.get_formatted_message(
                non_existent_object_identifier=self.CHANNEL_NAME,
            )

        super().__init__(message)


class RolesChannelDoesNotExistError(ChannelDoesNotExistError):
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


class GeneralChannelDoesNotExistError(ChannelDoesNotExistError):
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
