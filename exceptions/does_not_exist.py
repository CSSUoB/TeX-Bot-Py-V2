"""Custom exception classes to be raised when retrieved Discord objects do not exist."""

import abc
from typing import TYPE_CHECKING, override

from typed_classproperties import classproperty

from .base import BaseDoesNotExistError, BaseTeXBotError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

__all__: "Sequence[str]" = (
    "ApplicantRoleDoesNotExistError",
    "ArchivistRoleDoesNotExistError",
    "ChannelDoesNotExistError",
    "CommitteeElectRoleDoesNotExistError",
    "CommitteeRoleDoesNotExistError",
    "GeneralChannelDoesNotExistError",
    "GuestRoleDoesNotExistError",
    "GuildDoesNotExistError",
    "MemberRoleDoesNotExistError",
    "RoleDoesNotExistError",
    "RolesChannelDoesNotExistError",
    "RulesChannelDoesNotExistError",
)


class RulesChannelDoesNotExistError(BaseTeXBotError, ValueError):
    """Exception class to raise when the channel, marked as the rules channel, is missing."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "There is no channel marked as the rules channel."


class GuildDoesNotExistError(BaseDoesNotExistError):
    """Exception class to raise when a required Discord guild is missing."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "Server with given ID does not exist or is not accessible to the bot."

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1011"

    @classproperty
    @override
    def DOES_NOT_EXIST_TYPE(cls) -> str:
        return "guild"

    @override
    def __init__(self, message: str | None = None, guild_id: int | None = None) -> None:
        """Initialise a new DoesNotExist exception for a guild not existing."""
        self.guild_id: int | None = guild_id

        if guild_id and not message:
            message = self.DEFAULT_MESSAGE.replace("given ID", f"ID '{self.guild_id}'")

        super().__init__(message)


class RoleDoesNotExistError(BaseDoesNotExistError, abc.ABC):
    """Exception class to raise when a required Discord role is missing."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return f'Role with name "{cls.ROLE_NAME}" does not exist.'

    @classproperty
    @override
    def DOES_NOT_EXIST_TYPE(cls) -> str:
        return "role"

    @classproperty
    @abc.abstractmethod
    def ROLE_NAME(cls) -> str:  # noqa: N802
        """The name of the Discord role that does not exist."""

    @override
    def __init__(self, message: str | None = None) -> None:
        """Initialise a new DoesNotExist exception for a role not existing."""
        HAS_DEPENDANTS: Final[bool] = bool(
            self.DEPENDENT_COMMANDS or self.DEPENDENT_TASKS or self.DEPENDENT_EVENTS
        )

        if not message and HAS_DEPENDANTS:
            message = self.get_formatted_message(non_existent_object_identifier=self.ROLE_NAME)

        super().__init__(message)


class CommitteeRoleDoesNotExistError(RoleDoesNotExistError):
    """Exception class to raise when the "Committee" Discord role is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1021"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
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
                "committee-handover",
            },
        )

    @classproperty
    @override
    def ROLE_NAME(cls) -> str:
        return "Committee"


class CommitteeElectRoleDoesNotExistError(RoleDoesNotExistError):
    """Exception class to raise when the "Committee-Elect" Discord role is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1026"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
        return frozenset({"handover"})

    @classproperty
    @override
    def ROLE_NAME(cls) -> str:
        return "Committee-Elect"


class GuestRoleDoesNotExistError(RoleDoesNotExistError):
    """Exception class to raise when the "Guest" Discord role is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1022"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
        return frozenset(
            {
                "induct",
                "stats",
                "archive",
                "ensure-members-inducted",
                "increment-year-channels",
            },
        )

    @classproperty
    @override
    def DEPENDENT_TASKS(cls) -> frozenset[str]:
        return frozenset({"send_get_roles_reminders"})

    @classproperty
    @override
    def ROLE_NAME(cls) -> str:
        return "Guest"


class MemberRoleDoesNotExistError(RoleDoesNotExistError):
    """Exception class to raise when the "Member" Discord role is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1023"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
        return frozenset({"makemember", "ensure-members-inducted", "annual-roles-reset"})

    @classproperty
    @override
    def ROLE_NAME(cls) -> str:
        return "Member"


class ArchivistRoleDoesNotExistError(RoleDoesNotExistError):
    """Exception class to raise when the "Archivist" Discord role is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1024"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
        return frozenset({"archive", "increment-year-channels"})

    @classproperty
    @override
    def ROLE_NAME(cls) -> str:
        return "Archivist"


class ApplicantRoleDoesNotExistError(RoleDoesNotExistError):
    """Exception class to raise when the "Applicant" Discord role is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1025"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
        return frozenset({"make_applicant"})

    @classproperty
    @override
    def ROLE_NAME(cls) -> str:
        return "Applicant"


class ChannelDoesNotExistError(BaseDoesNotExistError):
    """Exception class to raise when a required Discord channel is missing."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return f'Channel with name "{cls.CHANNEL_NAME}" does not exist.'

    @classproperty
    @override
    def DOES_NOT_EXIST_TYPE(cls) -> str:
        return "channel"

    @classproperty
    @abc.abstractmethod
    def CHANNEL_NAME(cls) -> str:  # noqa: N802
        """The name of the Discord channel that does not exist."""

    @override
    def __init__(self, message: str | None = None) -> None:
        """Initialise a new DoesNotExist exception for a role not existing."""
        HAS_DEPENDANTS: Final[bool] = bool(
            self.DEPENDENT_COMMANDS or self.DEPENDENT_TASKS or self.DEPENDENT_EVENTS
        )

        if not message and HAS_DEPENDANTS:
            message = self.get_formatted_message(
                non_existent_object_identifier=self.CHANNEL_NAME,
            )

        super().__init__(message)


class RolesChannelDoesNotExistError(ChannelDoesNotExistError):
    """Exception class to raise when the "Roles" Discord channel is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1031"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
        return frozenset({"writeroles"})

    @classproperty
    @override
    def CHANNEL_NAME(cls) -> str:
        return "roles"


class GeneralChannelDoesNotExistError(ChannelDoesNotExistError):
    """Exception class to raise when the "General" Discord channel is missing."""

    @classproperty
    @override
    def ERROR_CODE(cls) -> str:
        return "E1032"

    @classproperty
    @override
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
        return frozenset({"induct"})

    @classproperty
    @override
    def CHANNEL_NAME(cls) -> str:
        return "general"
