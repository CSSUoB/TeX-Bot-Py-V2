"""Contains cog classes for any make_member interactions."""

import logging
import re
from typing import TYPE_CHECKING, override

import discord
from discord.ui import Modal, View
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

__all__: "Sequence[str]" = (
    "MakeMemberCommandCog",
    "MakeMemberModalCommandCog",
    "MemberCountCommandCog",
)


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


class MakeMemberBaseCog(TeXBotBaseCog):
    """Base cog class for make member interactions."""

    async def _perform_make_member(
        self, user: discord.User | discord.Member, raw_group_member_id: str
    ) -> tuple[bool, str]:
        """Perform the actions to make a user a member."""
        member_role: discord.Role = await self.bot.member_role
        discord_member: discord.Member = await self.bot.get_main_guild_member(user)

        INVALID_GROUP_MEMBER_ID_MESSAGE: Final[str] = (
            f"{raw_group_member_id!r} is not a valid {self.bot.group_member_id_type} ID."
        )

        if not re.fullmatch(r"\A\d{7}\Z", raw_group_member_id):
            return False, INVALID_GROUP_MEMBER_ID_MESSAGE

        try:
            group_member_id: int = int(raw_group_member_id)
        except ValueError:
            return False, INVALID_GROUP_MEMBER_ID_MESSAGE

        if member_role in discord_member.roles:
            return (
                False,
                (
                    ":information_source: No changes made. "
                    "You're already a member - why are you trying this again? :information_source:"
                ),
            )

        if await GroupMadeMember.objects.filter(
            hashed_group_member_id=GroupMadeMember.hash_group_member_id(
                group_member_id, self.bot.group_member_id_type
            )
        ).aexists():
            return False, "This student ID has already been used."

        if not await is_id_a_community_group_member(member_id=group_member_id):
            return False, (
                f"You must be a member of {self.bot.group_full_name} "
                "to use this command.\n"
                f"The provided {_GROUP_MEMBER_ID_ARGUMENT_NAME} must match "
                f"the {self.bot.group_member_id_type} ID "
                f"that you purchased your {self.bot.group_short_name} membership with."
            )

        await discord_member.add_roles(
            member_role, reason=f"{discord_member} used TeX-Bot to become a member"
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

            try:
                guest_role: discord.Role = await self.bot.guest_role
            except GuestRoleDoesNotExistError:
                logger.warning(
                    '"/make-member" command used but the "Guest" role does not exist. '
                    'Some user\'s may now have the "Member" role without the "Guest" role. '
                    'Use the "/ensure-members-inducted" command to fix this issue.'
                )
            else:
                if guest_role not in discord_member.roles:
                    await discord_member.add_roles(
                        guest_role,
                        reason=f"{discord_member} used TeX-Bot to become a member.",
                    )

            try:
                applicant_role: discord.Role = await self.bot.applicant_role
            except ApplicantRoleDoesNotExistError:
                pass
            else:
                if applicant_role in discord_member.roles:
                    await discord_member.remove_roles(
                        applicant_role,
                        reason=f"{discord_member} used TeX-Bot to become a member.",
                    )

        return True, ""


class MakeMemberCommandCog(MakeMemberBaseCog):
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
        await ctx.defer(ephemeral=True)

        with ctx.typing():
            _, message = await self._perform_make_member(
                user=ctx.user, raw_group_member_id=raw_group_member_id
            )

            await ctx.followup.send(content=message, ephemeral=True)


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


class MakeMemberModalActual(Modal, MakeMemberBaseCog):
    """A discord.Modal containing a the input box for make member user interaction."""

    @override
    def __init__(self) -> None:
        super().__init__(title="Make Member Modal")
        self.add_item(
            discord.ui.InputText(
                label="Student ID",
                min_length=7,
                max_length=7,
                required=True,
                placeholder="1234567",
            )
        )

    @override
    async def callback(self, interaction: discord.Interaction) -> None:
        raw_student_id: str | None = self.children[0].value
        if not raw_student_id:
            await interaction.response.send_message(
                content="Invalid Student ID.", ephemeral=True
            )
            return

        if not interaction.user:
            await interaction.response.send_message(
                content="Something went wrong, contact a committee member if this persists.",
                ephemeral=True,
            )
            logger.debug(
                "Interaction user was unexpectedly None in MakeMemberModal. Interaction: %s",
                interaction.data,
            )
            return

        await interaction.response.defer(ephemeral=True)

        _, message = await self._perform_make_member(
            user=interaction.user, raw_group_member_id=raw_student_id
        )

        await interaction.followup.send(content=message, ephemeral=True)


class OpenMemberVerifyModalView(View):
    """A discord.View containing a button to open a new member verification modal."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify", style=discord.ButtonStyle.primary, custom_id="verify_new_member"
    )
    async def verify_new_member_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        await interaction.response.send_modal(MakeMemberModalActual())


class MakeMemberModalCommandCog(MakeMemberBaseCog):
    """Cog class that defines the "/make-member-modal" command and its call-back method."""

    @TeXBotBaseCog.listener()
    async def on_ready(self) -> None:
        """Add OpenMemberVerifyModalView to the bot's list of permanent views."""
        self.bot.add_view(OpenMemberVerifyModalView())

    async def _open_make_new_member_modal(
        self,
        button_callback_channel: discord.TextChannel | discord.DMChannel,
    ) -> None:
        await button_callback_channel.send(
            content="would you like to open the make member modal",
            view=OpenMemberVerifyModalView(),
        )

    @discord.slash_command(
        name="make-member-modal",
        description=(
            "prints a message with a button that allows users to open the make member modal, "
        ),
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def make_member_modal(
        self,
        ctx: "TeXBotApplicationContext",
    ) -> None:
        """
        Definition & callback response of the "make-member-modal" command.

        The "make-member-modal" command prints a message with a button that allows users
        to open the make member modal
        """
        await self._open_make_new_member_modal(
            button_callback_channel=ctx.channel,
        )

        await ctx.respond(
            content="The make member modal has been opened in this channel.",
            ephemeral=True,
        )
