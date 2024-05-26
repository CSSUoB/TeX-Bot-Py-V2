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

from exceptions.base import BaseDoesNotExistError, BaseErrorWithErrorCode, BaseTeXBotError
from exceptions.config_changes import (
    BotRequiresRestartAfterConfigChange,
    ImproperlyConfiguredError,
)
from exceptions.does_not_exist import (
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
from exceptions.guild import (
    DiscordMemberNotInMainGuildError,
    EveryoneRoleCouldNotBeRetrievedError,
)
from exceptions.messages import (
    InvalidMessagesJSONFileError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)
from exceptions.strike import NoAuditLogsStrikeTrackingError, StrikeTrackingError
