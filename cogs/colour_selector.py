"""Contains cog classes for the colour selector command."""

import logging
from typing import TYPE_CHECKING

import discord

from exceptions import (
    GuildDoesNotExistError,
    RoleNotFoundInMainGuildError,
)
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext


__all__: Sequence[str] = ("MemberColourSelectorCommandCog",)


logger: Final[Logger] = logging.getLogger("TeX-Bot")


COLOUR_ROLE_NAMES: Final[
    AbstractSet[str]
] = {  # TODO: Make this a config option in the future  # noqa: FIX002
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
        ctx: TeXBotAutocompleteContext,
    ) -> AbstractSet[discord.OptionChoice] | AbstractSet[str]:
        """Autocomplete function for the colour roles option of the colour selector command."""
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except GuildDoesNotExistError:
            return set()

        roles: set[discord.Role] = {
            role for role in main_guild.roles if role.name.lower() in COLOUR_ROLE_NAMES
        }

        if not ctx.value or ctx.value.startswith("@"):
            return {
                discord.OptionChoice(name=f"@{role.name}", value=str(role.id))
                for role in roles
            }

        return {discord.OptionChoice(name=role.name, value=str(role.id)) for role in roles}

    @discord.slash_command(
        name="select-colour-role", description="Select a colour role for yourself."
    )
    @discord.option(
        name="colour-role",
        description="The colour role you want to select.",
        autocomplete=discord.utils.basic_autocomplete(autocomplete_colour_roles),
        input_type=str,
        required=True,
        parameter_name="str_role_id",
    )
    @CommandChecks.check_interaction_user_in_main_guild
    @CommandChecks.check_interaction_user_has_member_role
    async def select_colour_role(
        self, ctx: TeXBotApplicationContext, str_role_id: str
    ) -> None:
        """
        Slash command for selecting a colour role for the user.

        Definition & callback response of the "select-colour-role" command.
        The "select-colour-role" command assigns a colour role to the member that used
        the command to allow them to change their display colour.
        """
        await ctx.defer(ephemeral=True)

        async with ctx.typing():
            if not ctx.interaction.user:
                await self.command_send_error(
                    ctx=ctx,
                    message=(
                        "Cannot assign colour role when interaction user was not available."
                    ),
                )
                return

            role_to_add: discord.Role
            try:
                role_to_add = await ctx.bot.get_role_from_str_id(str_role_id)
            except RoleNotFoundInMainGuildError:
                await ctx.followup.send(
                    "The specified role could not be found in the main guild. "
                    "Please use the autocomplete.",
                    ephemeral=True,
                )
                return
            except ValueError:
                await ctx.followup.send(
                    "The specified role ID is not a valid role ID. "
                    "Please use the autocomplete.",
                    ephemeral=True,
                )
                return

            if role_to_add.name.lower() not in COLOUR_ROLE_NAMES:
                await ctx.followup.send(
                    ":information_source: No changes made. "
                    f"{role_to_add.name} is not a valid colour role. "
                    ":information_source:"
                )
                return

            interaction_member: discord.Member = await self.bot.get_main_guild_member(
                ctx.interaction.user
            )

            roles_to_remove: list[discord.Role] = [
                role
                for role in interaction_member.roles
                if role.name.lower() in COLOUR_ROLE_NAMES
            ]

            if role_to_add in roles_to_remove:
                roles_to_remove.remove(role_to_add)

            if roles_to_remove:
                await interaction_member.remove_roles(
                    *roles_to_remove,
                    reason=(
                        f"{interaction_member} used TeX-Bot "
                        f'slash-command "/select-colour-role".'
                    ),
                )

            await interaction_member.add_roles(
                role_to_add,
                reason=(
                    f'{interaction_member} used TeX-Bot slash-command "/select-colour-role".'
                ),
            )

            await ctx.followup.send(
                f"Successfully gave you the {role_to_add.name} colour role!", ephemeral=True
            )
