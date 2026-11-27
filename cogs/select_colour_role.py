"""Contains cog classes for any select_colour_role interactions."""

__all__: Sequence[str] = ("SelectColourRoleCommandCog",)

import logging
lazy from collections.abc import Collection, Sequence
lazy from collections.abc import Set as AbstractSet
lazy from logging import Logger
lazy from typing import Final

import discord

from utils import CommandChecks, TeXBotBaseCog
lazy from exceptions import GuildDoesNotExistError, RoleNotFoundInMainGuildError
lazy from utils import TeXBotApplicationContext, TeXBotAutocompleteContext

logger: Final[Logger] = logging.getLogger("TeX-Bot")

# TODO: Make this a config option in the future  # noqa: FIX002
COLOUR_ROLE_NAMES: Final[AbstractSet[str]] = {
    "og-green",
    "pink",
    "orange",
    "purple",
    "new-green",
    "yellow",
    "red",
}


class SelectColourRoleCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/select-colour-role" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_colour_roles(
        ctx: TeXBotAutocompleteContext,
    ) -> AbstractSet[discord.OptionChoice] | AbstractSet[str]:
        """Autocomplete callable that generates the set of selectable colour roles."""
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
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_colour_roles),
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
        Definition & callback response of the "select_colour_role" command.

        The "select_colour_role" command assigns a colour role to the member that used
        the command to allow them to change their display colour.
        """
        await ctx.defer(ephemeral=True)

        async with ctx.typing():
            missing_colour_role_names: AbstractSet[str] = COLOUR_ROLE_NAMES - {
                role.name.lower() for role in self.bot.main_guild.roles
            }
            if missing_colour_role_names:
                logger.warning(
                    "Colour roles %s could not be found.",
                    ", ".join(sorted(missing_colour_role_names)),
                )

            try:
                role_to_add: discord.Role = await self.bot.get_role_from_str_id(str_role_id)
            except RoleNotFoundInMainGuildError:
                await self.command_send_error(
                    ctx,
                    message=(
                        "The specified role could not be found "
                        f"in the {self.bot.group_short_name} Discord server. "
                        "Please use the autocomplete."
                    ),
                )
                return
            except ValueError:
                await self.command_send_error(
                    ctx,
                    message=(
                        "The specified role ID is not a valid role ID. "
                        "Please use the autocomplete."
                    ),
                )
                return

            if role_to_add.name.lower() not in COLOUR_ROLE_NAMES:
                await ctx.followup.send(
                    content=(
                        ":information_source: No changes made. "
                        f"{role_to_add.name} is not a valid colour role. "
                        ":information_source:"
                    ),
                    ephemeral=True,
                )
                return

            interaction_member: discord.Member = await self.bot.get_main_guild_member(ctx.user)

            roles_to_remove: Collection[discord.Role] = [
                role
                for role in interaction_member.roles
                if role.name.lower() in COLOUR_ROLE_NAMES and role != role_to_add
            ]

            member_already_has_role_to_add: bool = role_to_add in interaction_member.roles

            if member_already_has_role_to_add and not roles_to_remove:
                await ctx.followup.send(
                    content=(
                        ":information_source: No changes made. "
                        f"You already have the {role_to_add.name} colour role. "
                        ":information_source:"
                    ),
                    ephemeral=True,
                )
                return

            SELECT_COLOUR_ROLE_AUDIT_MESSAGE: Final[str] = (
                f'{interaction_member} used TeX-Bot slash-command "/select-colour-role".'
            )

            if not member_already_has_role_to_add:
                await interaction_member.add_roles(
                    role_to_add, reason=SELECT_COLOUR_ROLE_AUDIT_MESSAGE
                )

            await interaction_member.remove_roles(
                *roles_to_remove, reason=SELECT_COLOUR_ROLE_AUDIT_MESSAGE
            )

            await ctx.followup.send(
                content=(
                    (
                        f"You already have the {role_to_add.name} colour role, "
                        "so your other colour roles have been removed."
                    )
                    if member_already_has_role_to_add
                    else f"Successfully gave you the {role_to_add.name} colour role!"
                ),
                ephemeral=True,
            )
