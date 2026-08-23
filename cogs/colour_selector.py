"""Contains cog classes for the colour selector command."""

import logging
from typing import TYPE_CHECKING

import discord

from exceptions import DiscordMemberNotInMainGuildError
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext


__all__: "Sequence[str]" = ("MemberColourSelectorCommandCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


colour_role_names: "Final[AbstractSet[str]]" = {
    "green",
    "blue",
    "red",
    "yellow",
    "orange",
    "purple",
    "pink",
}


class MemberColourSelectorCommandCog(TeXBotBaseCog):
    """Cog class for the colour selector command."""

    @staticmethod
    async def autocomplete_colour_roles(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete function for the colour roles option of the colour selector command."""
        return {
            discord.OptionChoice(
                name=role.name,
                value=role.id,
            )
            for role in ctx.bot.main_guild.roles
            if role.name.lower() in colour_role_names
        }

    @discord.slash_command(
        name="member-colour-select",
        description="Select a colour role for yourself.",
    )
    @discord.option(
        name="colour-role",
        description="The colour role you want to select.",
        autocomplete=discord.utils.basic_autocomplete(autocomplete_colour_roles),
        input_type=str,
        required=True,
        parameter_name="role_id_str",
    )
    @CommandChecks.check_interaction_user_in_main_guild
    async def member_colour_select(
        self, ctx: "TeXBotApplicationContext", role_id_str: str
    ) -> None:
        """Slash command for selecting a colour role for the user."""
        # NOTE: Shortcut accessors are placed at the top of the function so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = ctx.bot.main_guild
        interaction_member: discord.Member | discord.User | None = ctx.interaction.user

        role_to_add: discord.Role | None = discord.utils.get(
            main_guild.roles, id=int(role_id_str)
        )

        if not role_to_add or not interaction_member:
            await ctx.respond(
                "The role you selected does not exist. Please use the autocomplete.",
                ephemeral=True,
            )
            return

        if isinstance(interaction_member, discord.User):
            try:
                fetched_member: discord.Member = await ctx.bot.get_main_guild_member(
                    interaction_member
                )
            except DiscordMemberNotInMainGuildError:
                await ctx.respond(
                    "You are not a member of the main guild. "
                    "Please join the main guild to use this command.",
                    ephemeral=True,
                )
                return

            interaction_member = fetched_member

        for role in interaction_member.roles:
            if role.name.lower() in colour_role_names:
                await interaction_member.remove_roles(role)

        await interaction_member.add_roles(
            role_to_add,
            reason=f"{interaction_member.global_name} used TeX-Bot /member_colour_select.",
        )
