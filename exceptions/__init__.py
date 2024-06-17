"""Exception classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "ApplicantRoleDoesNotExistError",
    "ArchivistRoleDoesNotExistError",
    "ChannelDoesNotExistError",
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
    "BotRequiresRestartAfterConfigChange",
    "ChangingSettingWithRequiredSiblingError",
    "ErrorCodeCouldNotBeIdentifiedError",
    "UnknownDjangoError",
)


from .config_changes import (
    BotRequiresRestartAfterConfigChange,
    ChangingSettingWithRequiredSiblingError,
)
from .custom_django import UnknownDjangoError
from .does_not_exist import (
    ApplicantRoleDoesNotExistError,
    ArchivistRoleDoesNotExistError,
    ChannelDoesNotExistError,
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
