"""
Contains all cogs.

Cogs are attachable modules that are loaded onto the discord.Bot instance. There are separate
cogs for each activity.
"""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "ArchiveCommandCog",
    "GetTokenAuthorisationCommandCog",
    "CommandErrorCog",
    "DeleteAllCommandsCog",
    "EditMessageCommandCog",
    "EnsureMembersInductedCommandCog",
    "MakeApplicantSlashCommandCog",
    "MakeApplicantContextCommandsCog",
    "CommitteeHandoverCommandCog",
    "AnnualRolesResetCommandCog",
    "InductSlashCommandCog",
    "InductSendMessageCog",
    "InductContextCommandsCog",
    "KillCommandCog",
    "MakeMemberCommandCog",
    "AnnualYearChannelsIncrementCommandCog",
    "PingCommandCog",
    "ClearRemindersBacklogTaskCog",
    "RemindMeCommandCog",
    "SendGetRolesRemindersTaskCog",
    "SendIntroductionRemindersTaskCog",
    "SourceCommandCog",
    "StartupCog",
    "StatsCommandsCog",
    "ManualModerationCog",
    "StrikeCommandCog",
    "StrikeContextCommandsCog",
    "WriteRolesCommandCog",
    "setup",
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
from .strike import ManualModerationCog, StrikeCommandCog, StrikeContextCommandsCog
from .write_roles import WriteRolesCommandCog

if TYPE_CHECKING:
    from collections.abc import Iterable

    from utils import TeXBotBaseCog


def setup(bot: TeXBot) -> None:
    """Add all the cogs to the bot, at bot startup."""
    cogs: Iterable[type[TeXBotBaseCog]] = (
        ArchiveCommandCog,
        GetTokenAuthorisationCommandCog,
        CommandErrorCog,
        DeleteAllCommandsCog,
        EditMessageCommandCog,
        EnsureMembersInductedCommandCog,
        CommitteeHandoverCommandCog,
        AnnualRolesResetCommandCog,
        InductSlashCommandCog,
        InductSendMessageCog,
        AnnualYearChannelsIncrementCommandCog,
        InductContextCommandsCog,
        KillCommandCog,
        MakeApplicantSlashCommandCog,
        MakeApplicantContextCommandsCog,
        MakeMemberCommandCog,
        PingCommandCog,
        ClearRemindersBacklogTaskCog,
        RemindMeCommandCog,
        SendGetRolesRemindersTaskCog,
        SendIntroductionRemindersTaskCog,
        SourceCommandCog,
        StartupCog,
        StatsCommandsCog,
        ManualModerationCog,
        StrikeCommandCog,
        StrikeContextCommandsCog,
        WriteRolesCommandCog,
    )
    Cog: type[TeXBotBaseCog]
    for Cog in cogs:
        bot.add_cog(Cog(bot))
