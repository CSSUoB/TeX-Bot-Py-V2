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
from utils.msl import (
    fetch_community_group_members_count,
    is_id_a_community_group_member,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext


__all__: "Sequence[str]" = ("MakeMemberCommandCog", "MemberCountCommandCog")


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


_GROUP_MEMBER_ID_ARGUMENT_DESCRIPTIVE_NAME: "Final[str]" = f"""{
    "Student"
    if (
        settings["_GROUP_FULL_NAME"]
        and (
            "computer science society" in settings["_GROUP_FULL_NAME"].lower()  # noqa: CAR180
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
    _GROUP_MEMBER_ID_ARGUMENT_DESCRIPTIVE_NAME.lower().replace(" ", "")
)


class MakeMemberCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/make-member" command and its call-back method."""

    @discord.slash_command(
        name="make-member",
        description=(
            "Gives you the Member role "
            f"when supplied with an appropriate {_GROUP_MEMBER_ID_ARGUMENT_DESCRIPTIVE_NAME}."
        ),
    )
    @discord.option(
        name=_GROUP_MEMBER_ID_ARGUMENT_NAME,
        description=(
            f"""Your UoB Student {
                "UoB Student"
                if (
                    settings["_GROUP_FULL_NAME"]
                    and (
                        "computer science society" in settings["_GROUP_FULL_NAME"].lower()  # noqa: CAR180
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
        parameter_name="raw_group_member_id",
    )
    @CommandChecks.check_interaction_user_in_main_guild
    async def make_member(
        self, ctx: "TeXBotApplicationContext", raw_group_member_id: str
    ) -> None:
        """
        Definition & callback response of the "make_member" command.

        The "make_member" command validates that the given member
        has purchased a valid membership to your community group,
        then gives the member the "Member" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function so that the exceptions they raise are displayed before any further errors may be sent
        member_role: discord.Role = await self.bot.member_role
        interaction_member: discord.Member = await ctx.bot.get_main_guild_member(ctx.user)

        INVALID_GROUP_MEMBER_ID_MESSAGE: Final[str] = (
            f"{raw_group_member_id!r} is not a valid {self.bot.group_member_id_type} ID."
        )

        if not re.fullmatch(r"\A\d{7}\Z", raw_group_member_id):
            await self.command_send_error(ctx, message=(INVALID_GROUP_MEMBER_ID_MESSAGE))
            return

        try:
            group_member_id: int = int(raw_group_member_id)
        except ValueError:
            await self.command_send_error(ctx, message=INVALID_GROUP_MEMBER_ID_MESSAGE)
            return

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

            if not await is_id_a_community_group_member(member_id=group_member_id):
                await self.command_send_error(
                    ctx,
                    message=(
                        f"You must be a member of {self.bot.group_full_name} "
                        "to use this command.\n"
                        f"The provided {_GROUP_MEMBER_ID_ARGUMENT_NAME} must match "
                        f"the {self.bot.group_member_id_type} ID "
                        f"that you purchased your {self.bot.group_short_name} membership with."
                    ),
                )
                return

            # NOTE: The "Member" role must be added to the user **before** the "Guest" role to ensure that the welcome message does not include the suggestion to purchase membership
            await interaction_member.add_roles(
                member_role, reason=f'{ctx.user} used TeX Bot slash-command: "/make-member"'
            )

            try:
                await GroupMadeMember.objects.acreate(group_member_id=raw_group_member_id)  # type: ignore[misc]
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
                    raise

            await ctx.followup.send(content="Successfully made you a member!", ephemeral=True)

            try:
                guest_role: discord.Role = await self.bot.guest_role
            except GuestRoleDoesNotExistError:
                logger.warning(
                    '"/make-member" command used but the "Guest" role does not exist. '
                    'Some user\'s may now have the "Member" role without the "Guest" role. '
                    'Use the "/ensure-members-inducted" command to fix this issue.'
                )
            else:
                if guest_role not in interaction_member.roles:
                    await interaction_member.add_roles(
                        guest_role,
                        reason=f'{ctx.user} used TeX Bot slash-command: "/make-member"',
                    )
            applicant_role: discord.Role | None
            try:
                applicant_role = await ctx.bot.applicant_role
            except ApplicantRoleDoesNotExistError:
                applicant_role = None

            if applicant_role and applicant_role in interaction_member.roles:
                await interaction_member.remove_roles(
                    applicant_role,
                    reason=f'{ctx.user} used TeX Bot slash-command: "/make-member"',
                )


class MemberCountCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/member-count" command and its call-back method."""

    @discord.slash_command(
        name="member-count", description="Displays the number of members in the group."
    )
    async def member_count(self, ctx: "TeXBotApplicationContext") -> None:
        """Definition & callback response of the "member_count" command."""
        await ctx.defer(ephemeral=False)

        async with ctx.typing():
            await ctx.followup.send(
                content=(
                    f"{self.bot.group_full_name} has "
                    f"{await fetch_community_group_members_count()} members! :tada:"
                )
            )

