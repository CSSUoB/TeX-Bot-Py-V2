"""Contains cog classes for any config changing interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("ConfigChangeCommandsCog",)


from typing import Final

import discord

import config
from config import ConfigSettingHelp, LogLevels
from utils import (
    CommandChecks,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)


class ConfigChangeCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/config" command group and command call-back methods."""

    change_config: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="config",
        description="Display, edit and get help about TeX-Bot's configuration.",
    )

    @staticmethod
    async def autocomplete_get_settings_names(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """Autocomplete callable that generates the set of available settings names."""
        if not ctx.interaction.user:
            return set()

        if not await ctx.bot.check_user_has_committee_role(ctx.interaction.user):
            return set()

        return {
            discord.OptionChoice(name=setting_name, value=setting_name)
            for setting_name
            in config.CONFIG_SETTINGS_HELPS
        }

    @staticmethod
    async def autocomplete_get_example_setting_values(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice | str]:  # noqa: E501
        """Autocomplete callable that generates example values for a configuration setting."""
        if not ctx.interaction.user or "setting" not in ctx.options:
            return set()

        if not await ctx.bot.check_user_has_committee_role(ctx.interaction.user):
            return set()

        if ":log-level" in ctx.options["setting"]:
            return set(log_level.value for log_level in LogLevels)

        return {discord.OptionChoice("hi", "hi"), discord.OptionChoice("wow", "wow")}

    @change_config.command(
        name="get",
        description="Display the current value of a configuration setting.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="setting",
        description="The name of the configuration setting value to retrieve.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_settings_names),  # type: ignore[arg-type]
        required=True,
        parameter_name="config_setting_name",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get_config_value(self, ctx: TeXBotApplicationContext, config_setting_name: str) -> None:  # noqa: E501
        """Definition & callback response of the "get_config_value" command."""
        if config_setting_name not in config.CONFIG_SETTINGS_HELPS:
            await self.command_send_error(
                ctx,
                f"Invalid setting: {config_setting_name!r}",
            )
            return

        config_setting_value: str | None = config.view_single_config_setting_value(
            config_setting_name,
        )

        if isinstance(config_setting_value, str):
            config_setting_value = config_setting_value.strip()

        CONFIG_SETTING_IS_SECRET: Final[bool] = bool(
            "token" in config_setting_name
            or "cookie" in config_setting_name
            or "secret" in config_setting_name  # noqa: COM812
        )

        await ctx.respond(
            (
                f"`{config_setting_name.replace("`", "\\`")}` "
                f"{
                    "**cannot be viewed**." if CONFIG_SETTING_IS_SECRET else (
                        f"**=** `{config_setting_value.replace("`", "\\`")}`"
                        if config_setting_value
                        else "**is not set**."
                    )
                }"
            ),
            ephemeral=True,
        )

    @change_config.command(
        name="help",
        description="Show the description of what a given configuration setting does.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="setting",
        description="The name of the configuration setting to show the description of.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_settings_names),  # type: ignore[arg-type]
        required=True,
        parameter_name="config_setting_name",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def help_config_setting(self, ctx: TeXBotApplicationContext, config_setting_name: str) -> None:  # noqa: E501
        """Definition & callback response of the "help_config_setting" command."""
        if config_setting_name not in config.CONFIG_SETTINGS_HELPS:
            await self.command_send_error(
                ctx,
                f"Invalid setting: {config_setting_name!r}",
            )
            return

        config_setting_help: ConfigSettingHelp = config.CONFIG_SETTINGS_HELPS[
            config_setting_name
        ]

        # noinspection PyProtectedMember
        await ctx.respond(
            (
                f"## `{
                    config_setting_name.replace("`", "\\`")
                }`\n"
                f"{
                    config_setting_help.description.replace(
                        "**`@TeX-Bot`**",
                        self.bot.user.mention if self.bot.user else "**`@TeX-Bot`**",
                    ).replace(
                        "TeX-Bot",
                        self.bot.user.mention if self.bot.user else "**`@TeX-Bot`**",
                    ).replace(
                        "the bot",
                        self.bot.user.mention if self.bot.user else "**`@TeX-Bot`**",
                    )
                }\n\n"
                f"{
                    f"{config_setting_help.value_type_message}\n\n"
                    if config_setting_help.value_type_message
                    else ""
                }"
                f"This setting is **{
                    "required" if config_setting_help.required else "optional"
                }**.\n\n"
                f"{
                    f"The default value for this setting is: `{
                        config_setting_help.default.replace("`", "\\`")
                    }`"
                    if config_setting_help.default
                    else ""
                }"
            ),
            ephemeral=True,
        )

    @change_config.command(
        name="set",
        description="Assign a new value to the specified configuration setting.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="setting",
        description="The name of the configuration setting to assign a new value to.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_settings_names),  # type: ignore[arg-type]
        required=True,
        parameter_name="config_setting_name",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="value",
        description="The new value to assign to the specified configuration setting.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_example_setting_values),  # type: ignore[arg-type]
        required=True,
        parameter_name="new_config_value",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def set_config_value(self, ctx: TeXBotApplicationContext, config_setting_name: str, new_config_value: str) -> None:  # noqa: E501
        """Definition & callback response of the "set_config_value" command."""
        if config_setting_name not in config.CONFIG_SETTINGS_HELPS:
            await self.command_send_error(
                ctx,
                f"Invalid setting: {config_setting_name!r}",
            )
            return

        config.assign_single_config_setting_value(config_setting_name)

        await ctx.respond(
            (
                f"Successfully updated setting: `{
                    config_setting_name.replace("`", "\\`")
                }`."
            ),
            ephemeral=True,
        )
