"""Contains cog classes for any make_member interactions."""

import contextlib
import logging
import re
from typing import TYPE_CHECKING

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError

from config import settings
from db.core.models import GroupMadeMember
from exceptions import (
    ApplicantRoleDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    GuestRoleDoesNotExistError,
)
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
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

ORGANISATION_ID: "Final[str]" = settings["ORGANISATION_ID"]
GROUP_NAME: "Final[str]" = settings["_GROUP_FULL_NAME"]
GROUPED_MEMBRS_URL: "Final[str]" = (
    f"https://guildofstudents.com/organisation/memberlist/{ORGANISATION_ID}/?sort=groups"
)
BASE_MEMBERS_URL: "Final[str]" = (
    f"https://guildofstudents.com/organisation/memberlist/{ORGANISATION_ID}"
)


class MakeMemberCommandCog(TeXBotBaseCog):
    # noinspection SpellCheckingInspection
    """Cog class that defines the "/makemember" command and its call-back method."""

    # noinspection SpellCheckingInspection
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
    async def make_member(self, ctx: "TeXBotApplicationContext", group_member_id: str) -> None:  # type: ignore[misc]  # noqa: PLR0915
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

            GROUP_MEMBER_ID_IS_ALREADY_USED: Final[
                bool
            ] = await GroupMadeMember.objects.filter(
                hashed_group_member_id=GroupMadeMember.hash_group_member_id(
                    group_member_id, self.bot.group_member_id_type
                )
            ).aexists()
            if GROUP_MEMBER_ID_IS_ALREADY_USED:
                committee_mention: str = "committee"
                with contextlib.suppress(CommitteeRoleDoesNotExistError):
                    committee_mention = (await self.bot.committee_role).mention

                await ctx.followup.send(
                    content=(
                        ":information_source: No changes made. This student ID has already "
                        f"been used. Please contact a {committee_mention} member if this is "
                        "an error. :information_source:"
                    ),
                    ephemeral=True,
                )
                return

            guild_member_ids: set[str] = set()

            http_session: aiohttp.ClientSession = aiohttp.ClientSession(
                headers=REQUEST_HEADERS,
                cookies=REQUEST_COOKIES,
            )
            async with http_session, http_session.get(GROUPED_MEMBRS_URL) as http_response:
                response_html: str = await http_response.text()

            MEMBER_HTML_TABLE_IDS: Final[frozenset[str]] = frozenset(
                {
                    "ctl00_Main_rptGroups_ctl05_gvMemberships",
                    "ctl00_Main_rptGroups_ctl03_gvMemberships",
                    "ctl00_ctl00_Main_AdminPageContent_rptGroups_ctl03_gvMemberships",
                    "ctl00_ctl00_Main_AdminPageContent_rptGroups_ctl05_gvMemberships",
                },
            )
            table_id: str
            for table_id in MEMBER_HTML_TABLE_IDS:
                parsed_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
                    response_html,
                    "html.parser",
                ).find(
                    "table",
                    {"id": table_id},
                )

                if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
                    continue

                guild_member_ids.update(
                    row.contents[2].text
                    for row in parsed_html.find_all(
                        "tr",
                        {"class": ["msl_row", "msl_altrow"]},
                    )
                )

            guild_member_ids.discard("")
            guild_member_ids.discard("\n")
            guild_member_ids.discard(" ")

            if not guild_member_ids:
                await self.command_send_error(
                    ctx,
                    error_code="E1041",
                    logging_message=OSError(
                        "The guild member IDs could not be retrieved from "
                        "the MEMBERS_LIST_URL.",
                    ),
                )
                return

            if group_member_id not in guild_member_ids:
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
                member_role,
                reason='TeX Bot slash-command: "/makemember"',
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
                    raise

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

            applicant_role: discord.Role | None = None
            with contextlib.suppress(ApplicantRoleDoesNotExistError):
                applicant_role = await ctx.bot.applicant_role

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
            http_session: aiohttp.ClientSession = aiohttp.ClientSession(
                headers=REQUEST_HEADERS,
                cookies=REQUEST_COOKIES,
            )
            async with http_session, http_session.get(BASE_MEMBERS_URL) as http_response:
                response_html: str = await http_response.text()

            member_list_div: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
                response_html,
                "html.parser",
            ).find(
                "div",
                {"class": "memberlistcol"},
            )

            if member_list_div is None or isinstance(member_list_div, bs4.NavigableString):
                await self.command_send_error(
                    ctx=ctx,
                    error_code="E1041",
                    logging_message=OSError(
                        "The member count could not be retrieved from the MEMBERS_LIST_URL.",
                    ),
                )
                return

            if "showing 100 of" in member_list_div.text.lower():
                member_count: str = member_list_div.text.split(" ")[3]
                await ctx.followup.send(
                    content=f"{GROUP_NAME} has {member_count} members! :tada:",
                )
                return

            member_table: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
                response_html,
                "html.parser",
            ).find(
                "table",
                {"id": "ctl00_ctl00_Main_AdminPageContent_gvMembers"},
            )

            if member_table is None or isinstance(member_table, bs4.NavigableString):
                await self.command_send_error(
                    ctx=ctx,
                    error_code="E1041",
                    logging_message=OSError(
                        "The member count could not be retrieved from the MEMBERS_LIST_URL."
                    ),
                )
                return

            await ctx.followup.send(
                content=f"{GROUP_NAME} has {
                    len(member_table.find_all('tr', {'class': ['msl_row', 'msl_altrow']}))
                } members! :tada:"
            )
