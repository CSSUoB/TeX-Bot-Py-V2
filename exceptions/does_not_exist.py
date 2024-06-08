"""Custom exception classes to be raised when retrieved Discord objects do not exist."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "RulesChannelDoesNotExistError",
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

from .base import BaseDoesNotExistError, BaseTeXBotError


class RulesChannelDoesNotExistError(BaseTeXBotError, ValueError):
    """Exception class to raise when the channel, marked as the rules channel, is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401
        return "There is no channel marked as the rules channel."


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
                "kill",
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
        return frozenset({"send_get_roles_reminders"})

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
    """Exception class to raise when the "Applicant" discord role is missing."""

    @classproperty
    def ERROR_CODE(cls) -> str:  # noqa: N802, N805
        """The unique error code for users to tell admins about an error that occured."""  # noqa: D401
        return "E1025"

    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]: # noqa: N802, N805
        """
        The set of names of bot commands that require this Discord entity.

        This set being empty could mean thta all bot commands require this entity,
        or that none of them do.
        """  # noqa: D401
        return frozenset({"make_applicant"})

    @classproperty
    def ROLE_NAME(cls) -> str: # noqa: N802, N805
        """The name of the Discord role that does not exist."""  # noqa: D401
        return "Applicant"


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







