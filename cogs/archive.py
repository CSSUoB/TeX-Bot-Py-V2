"""Contains cog classes for any archival interactions."""

import logging
import re

import discord

from exceptions import BaseDoesNotExistError, UserNotInCSSDiscordServer
from utils import (
    CommandChecks,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)


class ArchiveCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/archive" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_categories(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable categories.

        The list of available selectable categories is unique to each member, and is used in
        any of the "archive" slash-command options that have a category input-type.
        """
        if not ctx.interaction.user:
            return set()

        try:
            css_guild: discord.Guild = ctx.bot.css_guild
            interaction_user: discord.Member = await ctx.bot.get_css_user(ctx.interaction.user)
            assert await ctx.bot.check_user_has_committee_role(interaction_user)
        except (AssertionError, BaseDoesNotExistError, UserNotInCSSDiscordServer):
            return set()

        return {
            discord.OptionChoice(name=category.name, value=str(category.id))
            for category
            in css_guild.categories
            if category.permissions_for(interaction_user).is_superset(
                discord.Permissions(send_messages=True, view_channel=True)
            )
        }

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="archive",
        description="Archives the selected category."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="category",
        description="The category to archive.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_categories),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_category_id"
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_css_guild
    async def archive(self, ctx: TeXBotApplicationContext, str_category_id: str) -> None:
        """
        Definition & callback response of the "archive" command.

        The "archive" command hides a given category from view of casual members unless they
        have the "Archivist" role.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        css_guild: discord.Guild = self.bot.css_guild
        interaction_member: discord.Member = await self.bot.get_css_user(ctx.user)
        committee_role: discord.Role = await self.bot.committee_role
        guest_role: discord.Role = await self.bot.guest_role
        member_role: discord.Role = await self.bot.member_role
        archivist_role: discord.Role = await self.bot.archivist_role
        everyone_role: discord.Role = await self.bot.get_everyone_role()

        if not re.match(r"\A\d{17,20}\Z", str_category_id):
            await self.command_send_error(
                ctx,
                message=f"{str_category_id!r} is not a valid category ID."
            )
            return

        category_id: int = int(str_category_id)

        category: discord.CategoryChannel | None = discord.utils.get(
            css_guild.categories,
            id=category_id
        )
        if not category:
            await self.command_send_error(
                ctx,
                message=f"Category with ID {str(category_id)!r} does not exist."
            )
            return

        if "archive" in category.name:
            await ctx.respond(
                (
                    ":information_source: No changes made. "
                    "Category has already been archived. :information_source:"
                ),
                ephemeral=True
            )
            return

        # noinspection PyUnreachableCode
        channel: (
                discord.VoiceChannel
                | discord.StageChannel
                | discord.TextChannel
                | discord.ForumChannel
                | discord.CategoryChannel
        )
        for channel in category.channels:
            try:
                channel_needs_committee_archiving: bool = (
                    channel.permissions_for(committee_role).is_superset(
                        discord.Permissions(view_channel=True)
                    ) and not channel.permissions_for(guest_role).is_superset(
                        discord.Permissions(view_channel=True)
                    )
                )
                channel_needs_normal_archiving: bool = channel.permissions_for(
                    guest_role
                ).is_superset(
                    discord.Permissions(view_channel=True)
                )
                if channel_needs_committee_archiving:
                    await channel.set_permissions(
                        everyone_role,
                        reason=f"{interaction_member.display_name} used \"/archive\".",
                        view_channel=False
                    )
                    await channel.set_permissions(
                        guest_role,
                        overwrite=None,
                        reason=f"{interaction_member.display_name} used \"/archive\"."
                    )
                    await channel.set_permissions(
                        member_role,
                        overwrite=None,
                        reason=f"{interaction_member.display_name} used \"/archive\"."
                    )
                    await channel.set_permissions(
                        committee_role,
                        overwrite=None,
                        reason=f"{interaction_member.display_name} used \"/archive\"."
                    )

                elif channel_needs_normal_archiving:
                    await channel.set_permissions(
                        everyone_role,
                        reason=f"{interaction_member.display_name} used \"/archive\".",
                        view_channel=False
                    )
                    await channel.set_permissions(
                        guest_role,
                        overwrite=None,
                        reason=f"{interaction_member.display_name} used \"/archive\"."
                    )
                    await channel.set_permissions(
                        member_role,
                        overwrite=None,
                        reason=f"{interaction_member.display_name} used \"/archive\"."
                    )
                    await channel.set_permissions(
                        committee_role,
                        reason=f"{interaction_member.display_name} used \"/archive\".",
                        view_channel=False
                    )
                    await channel.set_permissions(
                        archivist_role,
                        reason=f"{interaction_member.display_name} used \"/archive\".",
                        view_channel=True
                    )

                else:
                    await self.command_send_error(
                        ctx,
                        message=f"Channel {channel.mention} had invalid permissions"
                    )
                    logging.error(
                        "Channel %s had invalid permissions, so could not be archived.",
                        channel.name
                    )
                    return

            except discord.Forbidden:
                await self.command_send_error(
                    ctx,
                    message=(
                        "Bot does not have access to the channels in the selected category."
                    )
                )
                logging.error(
                    (
                        "Bot did not have access to the channels in the selected category: "
                        "%s."
                    ),
                    category.name
                )
                return

        await ctx.respond("Category successfully archived", ephemeral=True)
