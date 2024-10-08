"""
Contains all cogs.

Cogs are attachable modules that are loaded onto the discord.Bot instance. There are separate
cogs for each activity.
"""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "AnnualRolesResetCommandCog",
    "AnnualYearChannelsIncrementCommandCog",
    "ArchiveCommandCog",
    "ClearRemindersBacklogTaskCog",
    "CommandErrorCog",
    "CommitteeHandoverCommandCog",
    "DeleteAllCommandsCog",
    "EditMessageCommandCog",
    "EnsureMembersInductedCommandCog",
    "GetTokenAuthorisationCommandCog",
    "InductContextCommandsCog",
    "InductSendMessageCog",
    "InductSlashCommandCog",
    "KillCommandCog",
    "MakeApplicantContextCommandsCog",
    "MakeApplicantSlashCommandCog",
    "MakeMemberCommandCog",
    "ManualModerationCog",
    "PingCommandCog",
    "RemindMeCommandCog",
    "SendGetRolesRemindersTaskCog",
    "SendIntroductionRemindersTaskCog",
    "setup",
    "SourceCommandCog",
    "StartupCog",
    "StatsCommandsCog",
    "StrikeCommandCog",
    "StrikeUserCommandCog",
    "WriteRolesCommandCog",
)


from typing import TYPE_CHECKING

from utils import TeXBot

from .annual_handover_and_reset import (
    AnnualRolesResetCommandCog,
    AnnualYearChannelsIncrementCommandCog,
    CommitteeHandoverCommandCog,
)
from .archive import ArchiveCommandCog
from .command_error import CommandErrorCog
from .delete_all import DeleteAllCommandsCog
from .edit_message import EditMessageCommandCog
from .get_token_authorisation import GetTokenAuthorisationCommandCog
from .induct import (
    EnsureMembersInductedCommandCog,
    InductContextCommandsCog,
    InductSendMessageCog,
    InductSlashCommandCog,
)
from .kill import KillCommandCog
from .make_applicant import MakeApplicantContextCommandsCog, MakeApplicantSlashCommandCog
from .make_member import MakeMemberCommandCog
from .ping import PingCommandCog
from .remind_me import ClearRemindersBacklogTaskCog, RemindMeCommandCog
from .send_get_roles_reminders import SendGetRolesRemindersTaskCog
from .send_introduction_reminders import SendIntroductionRemindersTaskCog
from .source import SourceCommandCog
from .startup import StartupCog
from .stats import StatsCommandsCog
from .strike import ManualModerationCog, StrikeCommandCog, StrikeUserCommandCog
from .write_roles import WriteRolesCommandCog

if TYPE_CHECKING:
    from collections.abc import Iterable

    from utils import TeXBotBaseCog


def setup(bot: TeXBot) -> None:
    """Add all the cogs to the bot, at bot startup."""
    cogs: Iterable[type[TeXBotBaseCog]] = (
        AnnualRolesResetCommandCog,
        AnnualYearChannelsIncrementCommandCog,
        ArchiveCommandCog,
        ClearRemindersBacklogTaskCog,
        CommandErrorCog,
        CommitteeHandoverCommandCog,
        DeleteAllCommandsCog,
        EditMessageCommandCog,
        EnsureMembersInductedCommandCog,
        GetTokenAuthorisationCommandCog,
        InductContextCommandsCog,
        InductSendMessageCog,
        InductSlashCommandCog,
        KillCommandCog,
        MakeApplicantContextCommandsCog,
        MakeApplicantSlashCommandCog,
        MakeMemberCommandCog,
        ManualModerationCog,
        PingCommandCog,
        RemindMeCommandCog,
        SendGetRolesRemindersTaskCog,
        SendIntroductionRemindersTaskCog,
        SourceCommandCog,
        StartupCog,
        StatsCommandsCog,
        StrikeCommandCog,
        StrikeUserCommandCog,
        WriteRolesCommandCog,
    )
    Cog: type[TeXBotBaseCog]
    for Cog in cogs:
        bot.add_cog(Cog(bot))
