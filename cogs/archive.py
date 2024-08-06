"""Contains cog classes for any archival interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("ArchiveCommandCog",)


import logging
import re
from collections.abc import Set
from logging import Logger
from typing import Final

import discord

from exceptions.base import BaseDoesNotExistError
from utils import (
    AllChannelTypes,
    CommandChecks,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class ArchiveCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/archive" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_categories(ctx: TeXBotAutocompleteContext) -> Set[discord.OptionChoice] | Set[str]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable categories.

        The list of available selectable categories is unique to each member and is used in
        any of the "archive" slash-command options that have a category input-type.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except BaseDoesNotExistError:
            return set()

        return {
            discord.OptionChoice(name=category.name, value=str(category.id))
            for category
            in main_guild.categories
        }

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="archive-category",
        description="Archives the selected category.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="category",
        description="The category to archive.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_categories),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_category_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="allow-archivist-access",
        description="Whether to allow archivists to access the category.",
        input_type=bool,
        required=True,
        parameter_name="allow_archivist",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def archive_category(self, ctx: TeXBotApplicationContext, str_category_id: str, allow_archivist: bool) -> None:  # noqa: E501
        """
        Definition & callback response of the "archive" command.

        The "archive" command hides a given category from view of casual members unless they
        have the "Archivist" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        committee_role: discord.Role = await self.bot.committee_role
        guest_role: discord.Role = await self.bot.guest_role
        archivist_role: discord.Role = await self.bot.archivist_role
        everyone_role: discord.Role = await self.bot.get_everyone_role()

        if not re.fullmatch(r"\A\d{17,20}\Z", str_category_id):
            await self.command_send_error(
                ctx=ctx,
                message=f"{str_category_id!r} is not a valid category ID.",
            )
            return

        category_id: int = int(str_category_id)

        category: discord.CategoryChannel | None = discord.utils.get(
            main_guild.categories,
            id=category_id,
        )
        if not category:
            await self.command_send_error(
                ctx=ctx,
                message=f"Category with ID {str(category_id)!r} does not exist.",
            )
            return

        if "archive" in category.name:
            await ctx.respond(
                (
                    ":information_source: No changes made. "
                    "Category has already been archived. :information_source:"
                ),
                ephemeral=True,
            )
            return

        channel: AllChannelTypes
        for channel in category.channels:
            if isinstance(channel, discord.CategoryChannel):  # NOTE: Categories can not be placed inside other categories, so this will always be false, but is needed due to the typing of the method
                continue

            await channel.edit(sync_permissions=True)


        await category.set_permissions(guest_role, overwrite=None)
        await category.set_permissions(committee_role, overwrite=None)
        await category.set_permissions(everyone_role, overwrite=None)

        if allow_archivist:
            await category.set_permissions(
                target=archivist_role,
                read_messages=True,
                read_message_history=True,
            )

        await category.edit(name=f"archive-{category.name}")

        await ctx.respond("Category successfully archived", ephemeral=True)
