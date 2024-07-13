"""Exception classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
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
    "DiscordMemberNotInMainGuildError",
    "EveryoneRoleCouldNotBeRetrievedError",
    "StrikeTrackingError",
    "NoAuditLogsStrikeTrackingError",
    "MessagesJSONFileMissingKeyError",
    "MessagesJSONFileValueError",
    "InvalidMessagesJSONFileError",
    "ImproperlyConfiguredError",
    "RestartRequiredDueToConfigChange",
)


from .config_changes import (
    RestartRequiredDueToConfigChange,
    ImproperlyConfiguredError,
)
from .does_not_exist import (
    ApplicantRoleDoesNotExistError,
    ArchivistRoleDoesNotExistError,
    ChannelDoesNotExistError,
    CommitteeElectRoleDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    GeneralChannelDoesNotExistError,
    GuestRoleDoesNotExistError,
    GuildDoesNotExistError,
    MemberRoleDoesNotExistError,
    RoleDoesNotExistError,
    RolesChannelDoesNotExistError,
    RulesChannelDoesNotExistError,
)
from .guild import (
    DiscordMemberNotInMainGuildError,
    EveryoneRoleCouldNotBeRetrievedError,
)
from .messages import (
    InvalidMessagesJSONFileError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)
from .strike import NoAuditLogsStrikeTrackingError, StrikeTrackingError
