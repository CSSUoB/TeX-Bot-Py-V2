"""Contains cog classes for any archival interactions."""

import logging
import re
from typing import TYPE_CHECKING

import discord

from exceptions import DiscordMemberNotInMainGuildError
from exceptions.base import BaseDoesNotExistError
from utils import (
    CommandChecks,
    TeXBotBaseCog,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import (
        AllChannelTypes,
        TeXBotApplicationContext,
        TeXBotAutocompleteContext,
    )

__all__: "Sequence[str]" = ("ArchiveCommandCog",)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class ArchiveCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/archive" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_categories(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of available selectable categories.

        The list of available selectable categories is unique to each member and is used in
        any of the "archive" slash-command options that have a category input-type.
        """
        if not ctx.interaction.user:
            return set()

        try:
            if not await ctx.bot.check_user_has_committee_role(ctx.interaction.user):
                return set()

            main_guild: discord.Guild = ctx.bot.main_guild
            interaction_user: discord.Member = await ctx.bot.get_main_guild_member(
                ctx.interaction.user,
            )
        except (BaseDoesNotExistError, DiscordMemberNotInMainGuildError):
            return set()

        return {
            discord.OptionChoice(name=category.name, value=str(category.id))
            for category in main_guild.categories
            if category.permissions_for(interaction_user).is_superset(
                discord.Permissions(send_messages=True, view_channel=True),
            )
        }

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="archive",
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
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def archive(self, ctx: "TeXBotApplicationContext", str_category_id: str) -> None:  # type: ignore[misc]
        """
        Definition & callback response of the "archive" command.

        The "archive" command hides a given category from view of casual members unless they
        have the "Archivist" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        interaction_member: discord.Member = await self.bot.get_main_guild_member(ctx.user)
        committee_role: discord.Role = await self.bot.committee_role
        guest_role: discord.Role = await self.bot.guest_role
        member_role: discord.Role = await self.bot.member_role
        archivist_role: discord.Role = await self.bot.archivist_role
        everyone_role: discord.Role = await self.bot.get_everyone_role()

        if not re.fullmatch(r"\A\d{17,20}\Z", str_category_id):
            await self.command_send_error(
                ctx,
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
                ctx,
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
            try:
                CHANNEL_NEEDS_COMMITTEE_ARCHIVING: bool = channel.permissions_for(
                    committee_role
                ).is_superset(
                    discord.Permissions(view_channel=True),
                ) and not channel.permissions_for(guest_role).is_superset(
                    discord.Permissions(view_channel=True),
                )
                CHANNEL_NEEDS_NORMAL_ARCHIVING: bool = channel.permissions_for(
                    guest_role
                ).is_superset(
                    discord.Permissions(view_channel=True),
                )
                if CHANNEL_NEEDS_COMMITTEE_ARCHIVING:
                    await channel.set_permissions(
                        everyone_role,
                        reason=f'{interaction_member.display_name} used "/archive".',
                        view_channel=False,
                    )
                    await channel.set_permissions(
                        guest_role,
                        overwrite=None,
                        reason=f'{interaction_member.display_name} used "/archive".',
                    )
                    await channel.set_permissions(
                        member_role,
                        overwrite=None,
                        reason=f'{interaction_member.display_name} used "/archive".',
                    )
                    await channel.set_permissions(
                        committee_role,
                        overwrite=None,
                        reason=f'{interaction_member.display_name} used "/archive".',
                    )

                elif CHANNEL_NEEDS_NORMAL_ARCHIVING:
                    await channel.set_permissions(
                        everyone_role,
                        reason=f'{interaction_member.display_name} used "/archive".',
                        view_channel=False,
                    )
                    await channel.set_permissions(
                        guest_role,
                        overwrite=None,
                        reason=f'{interaction_member.display_name} used "/archive".',
                    )
                    await channel.set_permissions(
                        member_role,
                        overwrite=None,
                        reason=f'{interaction_member.display_name} used "/archive".',
                    )
                    await channel.set_permissions(
                        committee_role,
                        reason=f'{interaction_member.display_name} used "/archive".',
                        view_channel=False,
                    )
                    await channel.set_permissions(
                        archivist_role,
                        reason=f'{interaction_member.display_name} used "/archive".',
                        view_channel=True,
                    )

                else:
                    await self.command_send_error(
                        ctx,
                        message=f"Channel {channel.mention} had invalid permissions",
                    )
                    logger.error(
                        "Channel %s had invalid permissions, so could not be archived.",
                        channel.name,
                    )
                    return

            except discord.Forbidden:
                await self.command_send_error(
                    ctx,
                    message=(
                        "TeX-Bot does not have access to "
                        "the channels in the selected category."
                    ),
                )
                logger.error(  # noqa: TRY400
                    (
                        "TeX-Bot did not have access to "
                        "the channels in the selected category: "
                        "%s."
                    ),
                    category.name,
                )
                return

        await ctx.respond("Category successfully archived", ephemeral=True)
