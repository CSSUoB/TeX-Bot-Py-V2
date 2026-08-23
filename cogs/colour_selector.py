"""Contains cog classes for the colour selector command."""

import logging
from typing import TYPE_CHECKING

import discord

from exceptions import DiscordMemberNotInMainGuildError, GuildDoesNotExistError
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext


__all__: "Sequence[str]" = ("MemberColourSelectorCommandCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


COLOUR_ROLE_NAMES: "Final[AbstractSet[str]]" = {  # TODO: Make this a config option in the future
    "og-green",
    "pink",
    "orange",
    "purple",
    "new-green",
    "yellow",
    "red",
}


class MemberColourSelectorCommandCog(TeXBotBaseCog):
    """Cog class for the colour selector command."""

    @staticmethod
    async def autocomplete_colour_roles(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete function for the colour roles option of the colour selector command."""
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except GuildDoesNotExistError:
            return set()

        return {
            discord.OptionChoice(
                name=role.name,
                value=str(role.id),
            )
            for role in main_guild.roles
            if role.name.lower() in COLOUR_ROLE_NAMES
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
    @CommandChecks.check_interaction_user_has_member_role
    async def member_colour_select(
        self, ctx: "TeXBotApplicationContext", role_id_str: str
    ) -> None:
        """Slash command for selecting a colour role for the user."""
        # NOTE: Shortcut accessors are placed at the top of the function so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = ctx.bot.main_guild
        interaction_member: discord.Member | discord.User | None = ctx.interaction.user

        if not interaction_member:
            await self.command_send_error(
                ctx=ctx,
                message="Interaction user was None for member-colour-select command execution."
            )
            return

        try:
            role_id_int = int(role_id_str)
        except ValueError:
            await self.command_send_error(
                ctx=ctx,
                message="Value entered was not a valid role ID."
            )
            return

        role_to_add: discord.Role | None = discord.utils.get(
            main_guild.roles, id=role_id_int
        )

        if not role_to_add:
            await ctx.respond(
                "The role you selected does not exist. Please use the autocomplete.",
                ephemeral=True,
            )
            return

        if role_to_add.name not in COLOUR_ROLE_NAMES:
            await ctx.respond(
                f"{role_to_add.name} is not a valid colour role. "
                "Please use the autocomplete."
            )
            return

        if isinstance(interaction_member, discord.User):
            try:
                fetched_member: discord.Member = await self.bot.get_main_guild_member(
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
            if role.name.lower() in COLOUR_ROLE_NAMES:
                await interaction_member.remove_roles(role)

        await interaction_member.add_roles(
            role_to_add,
            reason=f"{interaction_member} used TeX-Bot /member_colour_select.",
        )

        await ctx.respond(f"Successfully gave you the {role_to_add.name} colour role!")
