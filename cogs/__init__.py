"""
Contains all cogs.

Cogs are attachable modules that are loaded onto the discord.Bot instance. There are separate
cogs for each activity.
"""

from typing import TYPE_CHECKING

from .add_users_to_threads_and_channels import AddUsersToThreadsAndChannelsCommandCog
from .annual_handover_and_reset import (
    AnnualRolesResetCommandCog,
    AnnualYearChannelsIncrementCommandCog,
    CommitteeHandoverCommandCog,
)
from .archive import ArchiveCommandCog
from .command_error import CommandErrorCog
from .committee_actions_tracking import (
    CommitteeActionsTrackingContextCommandsCog,
    CommitteeActionsTrackingSlashCommandsCog,
)
from .delete_all import DeleteAllCommandsCog
from .edit_message import EditMessageCommandCog
from .get_token_authorisation import GetTokenAuthorisationCommandCog
from .induct import (
    EnsureMembersInductedCommandCog,
    InductContextCommandsCog,
    InductSendMessageCog,
    InductSlashCommandCog,
)
from .invite_link import InviteLinkCommandCog
from .kill import KillCommandCog
from .make_applicant import MakeApplicantContextCommandsCog, MakeApplicantSlashCommandCog
from .make_member import MakeMemberCommandCog, MemberCountCommandCog
from .ping import PingCommandCog
from .remind_me import ClearRemindersBacklogTaskCog, RemindMeCommandCog
from .send_get_roles_reminders import SendGetRolesRemindersTaskCog
from .send_introduction_reminders import SendIntroductionRemindersTaskCog
from .source import SourceCommandCog
from .startup import StartupCog
from .stats import StatsCommandsCog
from .strike import ManualModerationCog, StrikeCommandCog, StrikeContextCommandsCog
from .write_roles import WriteRolesCommandCog

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from utils import TeXBot, TeXBotBaseCog

__all__: "Sequence[str]" = (
    "AddUsersToThreadsAndChannelsCommandCog",
    "AnnualRolesResetCommandCog",
    "AnnualYearChannelsIncrementCommandCog",
    "ArchiveCommandCog",
    "ClearRemindersBacklogTaskCog",
    "CommandErrorCog",
    "CommitteeActionsTrackingContextCommandsCog",
    "CommitteeActionsTrackingSlashCommandsCog",
    "CommitteeHandoverCommandCog",
    "DeleteAllCommandsCog",
    "EditMessageCommandCog",
    "EnsureMembersInductedCommandCog",
    "GetTokenAuthorisationCommandCog",
    "InductContextCommandsCog",
    "InductSendMessageCog",
    "InductSlashCommandCog",
    "InviteLinkCommandCog",
    "KillCommandCog",
    "MakeApplicantContextCommandsCog",
    "MakeApplicantSlashCommandCog",
    "MakeMemberCommandCog",
    "ManualModerationCog",
    "MemberCountCommandCog",
    "PingCommandCog",
    "RemindMeCommandCog",
    "SendGetRolesRemindersTaskCog",
    "SendIntroductionRemindersTaskCog",
    "SourceCommandCog",
    "StartupCog",
    "StatsCommandsCog",
    "StrikeCommandCog",
    "StrikeContextCommandsCog",
    "WriteRolesCommandCog",
    "setup",
)


def setup(bot: "TeXBot") -> None:
    """Add all the cogs to the bot, at bot startup."""
    cogs: Iterable[type[TeXBotBaseCog]] = (
        AddUsersToThreadsAndChannelsCommandCog,
        AnnualRolesResetCommandCog,
        AnnualYearChannelsIncrementCommandCog,
        ArchiveCommandCog,
        ClearRemindersBacklogTaskCog,
        CommandErrorCog,
        CommitteeActionsTrackingSlashCommandsCog,
        CommitteeActionsTrackingContextCommandsCog,
        CommitteeHandoverCommandCog,
        DeleteAllCommandsCog,
        EditMessageCommandCog,
        EnsureMembersInductedCommandCog,
        GetTokenAuthorisationCommandCog,
        InductContextCommandsCog,
        InductSendMessageCog,
        InductSlashCommandCog,
        KillCommandCog,
        InviteLinkCommandCog,
        MakeApplicantContextCommandsCog,
        MakeApplicantSlashCommandCog,
        MakeMemberCommandCog,
        ManualModerationCog,
        MemberCountCommandCog,
        PingCommandCog,
        RemindMeCommandCog,
        SendGetRolesRemindersTaskCog,
        SendIntroductionRemindersTaskCog,
        SourceCommandCog,
        StartupCog,
        StatsCommandsCog,
        StrikeCommandCog,
        StrikeContextCommandsCog,
        WriteRolesCommandCog,
    )
    Cog: type[TeXBotBaseCog]
    for Cog in cogs:
        bot.add_cog(Cog(bot))
