"""Exception classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "BaseDoesNotExistError",
    "BaseErrorWithErrorCode",
    "BaseTeXBotError",
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
    "MessagesJSONFileMissingKeyError",
    "MessagesJSONFileValueError",
    "InvalidMessagesJSONFileError",
    "ImproperlyConfiguredError",
    "BotRequiresRestartAfterConfigChange",
)

from .base import BaseDoesNotExistError, BaseErrorWithErrorCode, BaseTeXBotError
from .config_changes import (
    BotRequiresRestartAfterConfigChange,
    ImproperlyConfiguredError,
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
from .messages import (
    InvalidMessagesJSONFileError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)
from .strike import NoAuditLogsStrikeTrackingError, StrikeTrackingError
