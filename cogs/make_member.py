"""Contains cog classes for any make_member interactions."""

import logging
import re
from typing import TYPE_CHECKING

import discord
from django.core.exceptions import ValidationError

from config import settings
from db.core.models import GroupMadeMember
from exceptions import ApplicantRoleDoesNotExistError, GuestRoleDoesNotExistError
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext

from utils.msl import get_membership_count, is_student_id_member

__all__: "Sequence[str]" = ("MakeMemberCommandCog", "MemberCountCommandCog")

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

_GROUP_MEMBER_ID_ARGUMENT_DESCRIPTIVE_NAME: "Final[str]" = f"""{
    "Student"
    if (
        settings["_GROUP_FULL_NAME"]
        and (
            "computer science society" in settings["_GROUP_FULL_NAME"].lower()
            or "css" in settings["_GROUP_FULL_NAME"].lower()
            or "uob" in settings["_GROUP_FULL_NAME"].lower()
            or "university of birmingham" in settings["_GROUP_FULL_NAME"].lower()
            or "uob" in settings["_GROUP_FULL_NAME"].lower()
            or (
                "bham" in settings["_GROUP_FULL_NAME"].lower()
                and "uni" in settings["_GROUP_FULL_NAME"].lower()
            )
        )
    )
    else "Member"
} ID"""

_GROUP_MEMBER_ID_ARGUMENT_NAME: "Final[str]" = (
    _GROUP_MEMBER_ID_ARGUMENT_DESCRIPTIVE_NAME.lower().replace(
        " ",
        "",
    )
)

REQUEST_HEADERS: "Final[Mapping[str, str]]" = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}

REQUEST_COOKIES: "Final[Mapping[str, str]]" = {
    ".ASPXAUTH": settings["MEMBERS_LIST_AUTH_SESSION_COOKIE"],
}

BASE_MEMBERS_URL: "Final[str]" = (
    f"https://guildofstudents.com/organisation/memberlist/{settings['ORGANISATION_ID']}"
)
GROUPED_MEMBERS_URL: "Final[str]" = f"{BASE_MEMBERS_URL}/?sort=groups"


class MakeMemberCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/makemember" command and its call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="makemember",
        description=(
            "Gives you the Member role "
            f"when supplied with an appropriate {_GROUP_MEMBER_ID_ARGUMENT_DESCRIPTIVE_NAME}."
        ),
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name=_GROUP_MEMBER_ID_ARGUMENT_NAME,
        description=(
            f"""Your UoB Student {
                "UoB Student"
                if (
                    settings["_GROUP_FULL_NAME"]
                    and (
                        "computer science society" in settings["_GROUP_FULL_NAME"].lower()
                        or "css" in settings["_GROUP_FULL_NAME"].lower()
                        or "uob" in settings["_GROUP_FULL_NAME"].lower()
                        or "university of birmingham" in settings["_GROUP_FULL_NAME"].lower()
                        or "uob" in settings["_GROUP_FULL_NAME"].lower()
                        or (
                            "bham" in settings["_GROUP_FULL_NAME"].lower()
                            and "uni" in settings["_GROUP_FULL_NAME"].lower()
                        )
                    )
                )
                else "Member"
            } ID"""
        ),
        input_type=str,
        required=True,
        max_length=7,
        min_length=7,
        parameter_name="group_member_id",
    )
    @CommandChecks.check_interaction_user_in_main_guild
    async def make_member(self, ctx: "TeXBotApplicationContext", group_member_id: str) -> None:  # type: ignore[misc]
        """
        Definition & callback response of the "make_member" command.

        The "make_member" command validates that the given member
        has purchased a valid membership to your community group,
        then gives the member the "Member" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        member_role: discord.Role = await self.bot.member_role
        interaction_member: discord.Member = await ctx.bot.get_main_guild_member(ctx.user)

        await ctx.defer(ephemeral=True)
        async with ctx.typing():
            if member_role in interaction_member.roles:
                await ctx.followup.send(
                    content=(
                        ":information_source: No changes made. You're already a member "
                        "- why are you trying this again? :information_source:"
                    ),
                    ephemeral=True,
                )
                return

            if not re.fullmatch(r"\A\d{7}\Z", group_member_id):
                await self.command_send_error(
                    ctx,
                    message=(
                        f"{group_member_id!r} is not a valid "
                        f"{self.bot.group_member_id_type} ID."
                    ),
                )
                return

            if await GroupMadeMember.objects.filter(
                hashed_group_member_id=GroupMadeMember.hash_group_member_id(
                    group_member_id, self.bot.group_member_id_type
                )
            ).aexists():
                await ctx.followup.send(
                    content=(
                        ":information_source: No changes made. This student ID has already "
                        f"been used. Please contact a {
                            await self.bot.get_mention_string(self.bot.committee_role)
                        } member if this is an error. :information_source:"
                    ),
                    ephemeral=True,
                )
                return

        if not await is_student_id_member(student_id=group_member_id):
            await self.command_send_error(
                ctx=ctx,
                message=(
                    f"You must be a member of {self.bot.group_full_name} "
                    "to use this command.\n"
                    f"The provided {_GROUP_MEMBER_ID_ARGUMENT_NAME} must match "
                    f"the {self.bot.group_member_id_type} ID "
                    f"that you purchased your {self.bot.group_short_name} membership with."
                ),
            )

        try:
            await GroupMadeMember.objects.acreate(group_member_id=group_member_id)  # type: ignore[misc]
        except ValidationError as create_group_made_member_error:
            error_is_already_exists: bool = (
                "hashed_group_member_id" in create_group_made_member_error.message_dict
                and any(
                    "already exists" in error
                    for error in create_group_made_member_error.message_dict[
                        "hashed_group_member_id"
                    ]
                )
            )
            if not error_is_already_exists:
                raise create_group_made_member_error from create_group_made_member_error

            await ctx.followup.send(content="Successfully made you a member!", ephemeral=True)

            try:
                guest_role: discord.Role = await self.bot.guest_role
            except GuestRoleDoesNotExistError:
                logger.warning(
                    '"/makemember" command used but the "Guest" role does not exist. '
                    'Some user\'s may now have the "Member" role without the "Guest" role. '
                    'Use the "/ensure-members-inducted" command to fix this issue.',
                )
            else:
                if guest_role not in interaction_member.roles:
                    await interaction_member.add_roles(
                        guest_role,
                        reason='TeX Bot slash-command: "/makemember"',
                    )
            applicant_role: discord.Role | None
            try:
                applicant_role = await ctx.bot.applicant_role
            except ApplicantRoleDoesNotExistError:
                applicant_role = None

            if applicant_role and applicant_role in interaction_member.roles:
                await interaction_member.remove_roles(
                    applicant_role,
                    reason='TeX Bot slash-command: "/makemember"',
                )


class MemberCountCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/membercount" command and its call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="membercount",
        description="Displays the number of members in the group.",
    )
    async def member_count(self, ctx: "TeXBotApplicationContext") -> None:  # type: ignore[misc]
        """Definition & callback response of the "member_count" command."""
        await ctx.defer(ephemeral=False)

        async with ctx.typing():
            await ctx.followup.send(
                content=f"{settings['GROUP_NAME']} has {await get_membership_count()} "
                "members! :tada:",
            )
