"""Exception classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
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
)

from .config_changes import (
    BotRequiresRestartAfterConfigChange,
)
from .does_not_exist import (
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
from .guild import (
    DiscordMemberNotInMainGuildError,
    EveryoneRoleCouldNotBeRetrievedError,
)
from .strike import NoAuditLogsStrikeTrackingError, StrikeTrackingError
