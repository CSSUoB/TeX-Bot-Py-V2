"""Exception classes & functions provided for use across the whole of the project."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = (
    "ApplicantRoleDoesNotExistError",
    "ArchivistRoleDoesNotExistError",
    "ChangingSettingWithRequiredSiblingError",
    "ChannelDoesNotExistError",
    "CommitteeElectRoleDoesNotExistError",
    "CommitteeRoleDoesNotExistError",
    "DiscordMemberNotInMainGuildError",
    "ErrorCodeCouldNotBeIdentifiedError",
    "EveryoneRoleCouldNotBeRetrievedError",
    "GeneralChannelDoesNotExistError",
    "GuestRoleDoesNotExistError",
    "GuildDoesNotExistError",
    "MemberRoleDoesNotExistError",
    "NoAuditLogsStrikeTrackingError",
    "RestartRequiredDueToConfigChange",
    "RoleDoesNotExistError",
    "RolesChannelDoesNotExistError",
    "RulesChannelDoesNotExistError",
    "StrikeTrackingError",
    "UnknownDjangoError",
)


from .config_changes import (
    ChangingSettingWithRequiredSiblingError,
    RestartRequiredDueToConfigChange,
)
from .custom_django import UnknownDjangoError
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
from .error_message_generation import ErrorCodeCouldNotBeIdentifiedError
from .guild import (
    DiscordMemberNotInMainGuildError,
    EveryoneRoleCouldNotBeRetrievedError,
)
from .strike import NoAuditLogsStrikeTrackingError, StrikeTrackingError
