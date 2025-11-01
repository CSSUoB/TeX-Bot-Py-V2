"""Contains cog classes for any archival interactions."""

import logging
import re
from typing import TYPE_CHECKING

import discord

from exceptions.base import BaseDoesNotExistError
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import AllChannelTypes, TeXBotApplicationContext, TeXBotAutocompleteContext

__all__: "Sequence[str]" = ("ArchiveCommandsCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class ArchiveCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/archive" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_non_archival_categories(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of available selectable categories.

        Returns the set of selectable categories.
        Only categories which do not contain the word "archive" are selectable.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except BaseDoesNotExistError:
            return set()

        return {
            discord.OptionChoice(name=category.name, value=str(category.id))
            for category in main_guild.categories
            if "archive" not in category.name.lower()
        }

    @staticmethod
    async def autocomplete_get_archival_categories(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of categories to hold archived channels.

        The set of categories only includes those that contain the word "archive".
        These are the categories that channels are to be placed into for archiving.
        It is assumed that the categories have the correct permission configuration.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except BaseDoesNotExistError:
            return set()

        return {
            discord.OptionChoice(name=category.name, value=str(category.id))
            for category in main_guild.categories
            if "archive" in category.name.lower()
        }

    @staticmethod
    async def autocomplete_get_non_archived_channels(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of channels that the user can archive.

        The list of channels will include all types of channels and categories, except those
        that have not been archived.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except BaseDoesNotExistError:
            return set()

        interaction_user: discord.Member | discord.User | None = ctx.interaction.user

        return {
            discord.OptionChoice(name=channel.name, value=str(channel.id))
            for channel in main_guild.channels
            if (
                not isinstance(channel, discord.CategoryChannel)  # noqa: CAR180
                and channel.category
                and "archive" not in channel.category.name.lower()
                and isinstance(interaction_user, discord.Member)
                and channel.permissions_for(interaction_user).read_messages
            )
        }

    @discord.slash_command(
        name="archive-category", description="Archives the selected category."
    )
    @discord.option(
        name="category",
        description="The category to archive.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(
            autocomplete_get_non_archival_categories
        ),
        required=True,
        parameter_name="str_category_id",
    )
    @discord.option(
        name="allow-archivist-access",
        description="Whether to allow archivists to access the category.",
        input_type=bool,
        required=True,
        parameter_name="allow_archivist",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def archive_category(
        self,
        ctx: "TeXBotApplicationContext",
        str_category_id: str,
        allow_archivist: bool,  # noqa: FBT001
    ) -> None:
        """
        Definition & callback response of the "archive-category" command.

        The "archive" command hides a given category from view of casual members unless they
        have the "Archivist" role. This can be overridden via a boolean parameter to allow
        for committee channels to be archived with the same command but not be visible.
        """
        # NOTE: Shortcut accessors are placed at the top of the function so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        archivist_role: discord.Role = await self.bot.archivist_role

        if not re.fullmatch(r"\A\d{17,20}\Z", str_category_id):
            await self.command_send_error(
                ctx, message=f"{str_category_id!r} is not a valid category ID."
            )
            return

        category_id: int = int(str_category_id)

        category: discord.CategoryChannel | None = discord.utils.get(
            main_guild.categories, id=category_id
        )
        if not category:
            await self.command_send_error(
                ctx, message=f"Category with ID {str(category_id)!r} does not exist."
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

        await ctx.defer(ephemeral=True)

        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            content=f"Archiving {category.name}...", ephemeral=True
        )

        channel: AllChannelTypes
        for channel in category.channels:
            # NOTE: Categories can not be placed inside other categories, so this will always be false, but is needed due to the typing of the method
            if isinstance(channel, discord.CategoryChannel):
                continue

            await channel.edit(sync_permissions=True)

        target: discord.Member | discord.Role
        for target in category.overwrites:
            await category.set_permissions(target=target, overwrite=None)

        everyone_role: discord.Role = await ctx.bot.get_everyone_role()
        await category.set_permissions(
            target=everyone_role,
            view_channel=False,
        )

        if allow_archivist:
            await category.set_permissions(
                target=archivist_role,
                view_channel=True,
                read_messages=True,
                read_message_history=True,
                send_messages=False,
            )

        await category.edit(name=f"archive-{category.name}")

        await category.edit(position=len(main_guild.categories))

        await initial_response.edit(
            content=f":white_check_mark: Category '{category.name}' successfully archived."
        )

    @discord.slash_command(
        name="archive-channel", description="Archives the selected channel."
    )
    @discord.option(
        name="channel",
        description="The channel to archive.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_non_archived_channels),
        required=True,
        parameter_name="str_channel_id",
    )
    @discord.option(
        name="category",
        description="The category to move the channel to.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_archival_categories),
        required=True,
        parameter_name="str_category_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def archive_channel(
        self, ctx: "TeXBotApplicationContext", str_channel_id: str, str_category_id: str
    ) -> None:
        """
        Definition & callback response of the "archive-channel" command.

        The "archive-channel" command moves the channel into the selected category
        and syncs the permissions to the category's permissions.
        """
        # NOTE: Shortcut accessors are placed at the top of the function so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild

        if not re.fullmatch(r"\A\d{17,20}\Z", str_channel_id):
            await self.command_send_error(
                ctx, message=f"{str_channel_id!r} is not a valid channel ID."
            )
            return

        channel_id: int = int(str_channel_id)

        channel: AllChannelTypes | None = discord.utils.get(main_guild.channels, id=channel_id)

        if not channel:
            await self.command_send_error(
                ctx, message=f"Channel with ID {str(channel_id)!r} does not exist."
            )
            return

        if isinstance(channel, discord.CategoryChannel):
            await self.command_send_error(
                ctx,
                message=(
                    "Supplied channel to archive is a category - "
                    "please use the archive-channel command to archive categories."
                ),
            )
            return

        if not re.fullmatch(r"\A\d{17,20}\Z", str_category_id):
            await self.command_send_error(
                ctx, message=f"{str_category_id!r} is not a valid category ID."
            )

        category_id: int = int(str_category_id)

        category: discord.CategoryChannel | None = discord.utils.get(
            main_guild.categories, id=category_id
        )

        if not category:
            await self.command_send_error(
                ctx, message=f"Category with ID {str(category_id)!r} does not exist."
            )
            return

        if len(category.channels) >= 50:
            await self.command_send_error(
                ctx,
                message=(
                    f"Category with ID {str(category_id)!r} is full. "
                    "Please select a different category."
                ),
            )
            return

        await channel.edit(category=category, sync_permissions=True)

        await ctx.respond(":white_check_mark: Channel successfully archived", ephemeral=True)
