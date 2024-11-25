"""Exception classes & functions provided for use across the whole of the project."""

from typing import TYPE_CHECKING

from .committee_actions import InvalidActionDescriptionError, InvalidActionTargetError
from .config_changes import (
    ImproperlyConfiguredError,
    RestartRequiredDueToConfigChange,
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

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "ApplicantRoleDoesNotExistError",
    "ArchivistRoleDoesNotExistError",
    "ChannelDoesNotExistError",
    "CommitteeElectRoleDoesNotExistError",
    "CommitteeRoleDoesNotExistError",
    "DiscordMemberNotInMainGuildError",
    "EveryoneRoleCouldNotBeRetrievedError",
    "GeneralChannelDoesNotExistError",
    "GuestRoleDoesNotExistError",
    "GuildDoesNotExistError",
    "ImproperlyConfiguredError",
    "InvalidActionDescriptionError",
    "InvalidActionTargetError",
    "InvalidMessagesJSONFileError",
    "MemberRoleDoesNotExistError",
    "MessagesJSONFileMissingKeyError",
    "MessagesJSONFileValueError",
    "NoAuditLogsStrikeTrackingError",
    "RestartRequiredDueToConfigChange",
    "RoleDoesNotExistError",
    "RolesChannelDoesNotExistError",
    "RulesChannelDoesNotExistError",
    "StrikeTrackingError",
)
