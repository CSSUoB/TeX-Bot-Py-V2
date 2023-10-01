import logging
import re

import discord

from cogs._utils import TeXBotAutocompleteContext, TeXBotCog
from exceptions import (
    ArchivistRoleDoesNotExist,
    CommitteeRoleDoesNotExist,
    GuestRoleDoesNotExist,
    GuildDoesNotExist,
    MemberRoleDoesNotExist
)


class ArchiveCommandCog(TeXBotCog):
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
            guild: discord.Guild = ctx.bot.css_guild
        except GuildDoesNotExist:
            return set()

        committee_role: discord.Role | None = await ctx.bot.committee_role
        if not committee_role:
            return set()

        interaction_member: discord.Member | None = guild.get_member(ctx.interaction.user.id)
        if not interaction_member:
            return set()

        if committee_role not in interaction_member.roles:
            return set()

        return {
            discord.OptionChoice(name=category.name, value=str(category.id))
            for category
            in guild.categories
            if category.permissions_for(interaction_member).is_superset(
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
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_categories),  # type: ignore[arg-type] # noqa: E501
        required=True,
        parameter_name="str_category_id"
    )
    async def archive(self, ctx: discord.ApplicationContext, str_category_id: str) -> None:
        """
        Definition & callback response of the "archive" command.

        The "archive" command hides a given category from view of casual members unless they
        have the "Archivist" role.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        committee_role: discord.Role | None = await self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                logging_message=CommitteeRoleDoesNotExist()
            )
            return

        guest_role: discord.Role | None = await self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                logging_message=GuestRoleDoesNotExist()
            )
            return

        member_role: discord.Role | None = await self.bot.member_role
        if not member_role:
            await self.send_error(
                ctx,
                error_code="E1023",
                logging_message=MemberRoleDoesNotExist()
            )
            return

        archivist_role: discord.Role | None = await self.bot.archivist_role
        if not archivist_role:
            await self.send_error(
                ctx,
                error_code="E1024",
                logging_message=ArchivistRoleDoesNotExist()
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = f"`{committee_role.mention}`"

            await self.send_error(
                ctx,
                message=f"Only {committee_role_mention} members can run this command."
            )
            return

        everyone_role: discord.Role | None = discord.utils.get(guild.roles, name="@everyone")
        if not everyone_role:
            await self.send_error(ctx, error_code="E1042")
            logging.error(
                "The reference to the \"@everyone\" role could not be correctly retrieved."
            )
            return

        if not re.match(r"\A\d{17,20}\Z", str_category_id):
            await self.send_error(
                ctx,
                message=f"\"{str_category_id}\" is not a valid category ID."
            )
            return

        category_id: int = int(str_category_id)

        category: discord.CategoryChannel | None = discord.utils.get(
            guild.categories,
            id=category_id
        )
        if not category:
            await self.send_error(
                ctx,
                message=f"Category with ID \"{category_id}\" does not exist."
            )
            return

        if "archive" in category.name:
            await ctx.respond(
                (
                    ":information_source: No changes made. Category has already been archived."
                    " :information_source:"
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
                    await self.send_error(
                        ctx,
                        message=f"Channel {channel.mention} had invalid permissions"
                    )
                    logging.error(
                        "Channel %s had invalid permissions, so could not be archived.",
                        channel.name
                    )
                    return

            except discord.Forbidden:
                await self.send_error(
                    ctx,
                    message=(
                        "Bot does not have access to the channels in the selected category."
                    )
                )
                logging.error(
                    (
                        "Bot did not have access to the channels in the selected category:"
                        " %s."
                    ),
                    category.name
                )
                return

        await ctx.respond("Category successfully archived", ephemeral=True)
