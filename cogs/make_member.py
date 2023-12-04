"""Contains cog classes for any make_member interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ["MakeMemberCommandCog"]

import contextlib
import logging
import re
from typing import Final

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError

from config import settings
from db.core.models import GroupMadeMember
from exceptions import CommitteeRoleDoesNotExist, GuestRoleDoesNotExist
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog


class MakeMemberCommandCog(TeXBotBaseCog):
    # noinspection SpellCheckingInspection
    """Cog class that defines the "/makemember" command and its call-back method."""

    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="makemember",
        description="Gives you the Member role when supplied with an appropriate Student ID."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="studentid",  # TODO: Rename
        description="Your UoB Student ID",  # TODO: Rename
        input_type=str,
        required=True,
        max_length=7,
        min_length=7,
        parameter_name="group_id"
    )
    @CommandChecks.check_interaction_user_in_css_guild
    async def make_member(self, ctx: TeXBotApplicationContext, group_id: str) -> None:
        """
        Definition & callback response of the "make_member" command.

        The "make_member" command validates that the given member has a valid CSS membership
        then gives the member the "Member" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        member_role: discord.Role = await self.bot.member_role
        interaction_member: discord.Member = await ctx.bot.get_css_user(ctx.user)

        if member_role in interaction_member.roles:
            await ctx.respond(
                (
                    ":information_source: No changes made. You're already a member "
                    "- why are you trying this again? :information_source:"
                ),
                ephemeral=True
            )
            return

        if not re.match(r"\A\d{7}\Z", group_id):
            await self.send_error(
                ctx,
                message=f"{group_id!r} is not a valid {self.bot.group_id_type} ID."
            )
            return

        group_id_is_already_used: bool = await GroupMadeMember.objects.filter(
            hashed_group_id=GroupMadeMember.hash_group_id(group_id, self.bot.group_id_type)
        ).aexists()
        if group_id_is_already_used:
            # noinspection PyUnusedLocal
            committee_mention: str = "committee"
            with contextlib.suppress(CommitteeRoleDoesNotExist):
                committee_mention = (await self.bot.roles_channel).mention

            await ctx.respond(
                (
                    ":information_source: No changes made. This student ID has already "
                    f"been used. Please contact a {committee_mention} member if this is "
                    "an error. :information_source:"
                ),
                ephemeral=True
            )
            return

        guild_member_ids: set[str] = set()

        request_headers: dict[str, str] = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        request_cookies: dict[str, str] = {
            ".ASPXAUTH": settings["MEMBERS_LIST_URL_SESSION_COOKIE"]
        }
        async with aiohttp.ClientSession(headers=request_headers, cookies=request_cookies) as http_session:  # noqa: E501, SIM117
            async with http_session.get(url=settings["MEMBERS_LIST_URL"]) as http_response:
                response_html: str = await http_response.text()

        MEMBER_HTML_TABLE_IDS: Final[frozenset[str]] = frozenset(  # TODO: Make abstract protocol (JSON retriever Vs HTML parser)
            {
                "ctl00_Main_rptGroups_ctl05_gvMemberships",
                "ctl00_Main_rptGroups_ctl03_gvMemberships"
            }
        )
        table_id: str
        for table_id in MEMBER_HTML_TABLE_IDS:
            parsed_html: bs4.Tag | None = BeautifulSoup(
                response_html,
                "html.parser"
            ).find(
                "table",
                {"id": table_id}
            )

            if parsed_html:
                guild_member_ids.update(
                    row.contents[2].text
                    for row
                    in parsed_html.find_all(
                        "tr",
                        {"class": ["msl_row", "msl_altrow"]}
                    )
                )

        guild_member_ids.discard("")
        guild_member_ids.discard("\n")
        guild_member_ids.discard(" ")

        if not guild_member_ids:
            await self.send_error(
                ctx,
                error_code="E1041",
                logging_message=OSError(
                    "The guild member IDs could not be retrieved from "
                    "the MEMBERS_LIST_URL."
                )
            )
            return

        if group_id not in guild_member_ids:
            await self.send_error(
                ctx,
                message=(
                    "You must be a member of The Computer Science Society "  # TODO: Fix full name
                    "to use this command.\n"
                    "The provided student ID must match the UoB student ID "  # TODO: Fix ID type names
                    f"that you purchased your {self.bot.group_name} membership with."
                )
            )
            return

        # NOTE: The "Member" role must be added to the user **before** the "Guest" role to ensure that the welcome message does not include the suggestion to purchase membership
        await interaction_member.add_roles(
            member_role,
            reason="TeX Bot slash-command: \"/makemember\""
        )

        try:
            await GroupMadeMember.objects.acreate(group_id=group_id)
        except ValidationError as create_group_made_member_error:
            error_is_already_exists: bool = (
                "hashed_group_id" in create_group_made_member_error.message_dict
                and any(
                    "already exists"
                    in error
                    for error
                    in create_group_made_member_error.message_dict["hashed_group_id"]
                )
            )
            if not error_is_already_exists:
                raise

        await ctx.respond("Successfully made you a member!", ephemeral=True)

        try:
            guest_role: discord.Role = await self.bot.guest_role
        except GuestRoleDoesNotExist:
            logging.warning(
                "\"/makemember\" command used but the \"Guest\" role does not exist. "
                "Some user's may now have the \"Member\" role without the \"Guest\" role. "
                "Use the \"/ensure-members-inducted\" command to fix this issue."
            )
        else:
            if guest_role not in interaction_member.roles:
                await interaction_member.add_roles(
                    guest_role,
                    reason="TeX Bot slash-command: \"/makemember\""
                )

        applicant_role: discord.Role | None = discord.utils.get(
            self.bot.css_guild.roles,
            name="Applicant"
        )
        if applicant_role and applicant_role in interaction_member.roles:
            await interaction_member.remove_roles(
                applicant_role,
                reason="TeX Bot slash-command: \"/makemember\""
            )
