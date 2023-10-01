"""
Contains all cogs.

Cogs are attachable modules that are loaded onto the discord.Bot instance. There are separate
cogs for each activity.
"""

from typing import TYPE_CHECKING

from cogs.archive import ArchiveCommandCog
from cogs.command_error import CommandErrorCog
from cogs.delete_all import DeleteAllCommandsCog
from cogs.edit_message import EditMessageCommandCog
from cogs.induct import (
    EnsureMembersInductedCommandCog,
    InductCommandCog,
    InductSendMessageCog,
    InductUserCommandsCog,
)
from cogs.kick_no_introduction_users import KickNoIntroductionUsersTaskCog
from cogs.make_member import MakeMemberCommandCog
from cogs.ping import PingCommandCog
from cogs.remind_me import ClearRemindersBacklogTaskCog, RemindMeCommandCog
from cogs.send_get_roles_reminders import SendGetRolesRemindersTaskCog
from cogs.send_introduction_reminders import SendIntroductionRemindersTaskCog
from cogs.source import SourceCommandCog
from cogs.startup import StartupCog
from cogs.stats import StatsCommandsCog
from cogs.write_roles import WriteRolesCommandCog
from utils import TeXBot

if TYPE_CHECKING:
    from collections.abc import Iterable

    from cogs._utils import TeXBotCog


def setup(bot: TeXBot) -> None:
    """Add all the cogs to the bot, at bot startup."""
    cogs: Iterable[type[TeXBotCog]] = (
        ArchiveCommandCog,
        CommandErrorCog,
        DeleteAllCommandsCog,
        EditMessageCommandCog,
        EnsureMembersInductedCommandCog,
        InductCommandCog,
        InductSendMessageCog,
        InductUserCommandsCog,
        KickNoIntroductionUsersTaskCog,
        MakeMemberCommandCog,
        PingCommandCog,
        ClearRemindersBacklogTaskCog,
        RemindMeCommandCog,
        SendGetRolesRemindersTaskCog,
        SendIntroductionRemindersTaskCog,
        SourceCommandCog,
        StartupCog,
        StatsCommandsCog,
        WriteRolesCommandCog,
    )
    Cog: type[TeXBotCog]
    for Cog in cogs:
        bot.add_cog(Cog(bot))
