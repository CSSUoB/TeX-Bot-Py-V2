"""Contains cog classes for any config changing interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("ConfigChangeCommandsCog",)


import discord
from typing import Final
import config
from utils import (
    CommandChecks,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
    TeXBotApplicationContext,
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
            in config.get_loaded_config_settings_names()
        }

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
    async def get_config_value(self, ctx: TeXBotApplicationContext, config_setting_name: str) -> None:
        """Definition & callback response of the "get_config_value" command."""
        if config_setting_name not in config.get_loaded_config_settings_names():
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

        CONFIG_SETTING_NEEDS_HIDING: Final[bool] = bool(
            "token" in config_setting_name
            or "cookie" in config_setting_name
            or "secret" in config_setting_name
        )

        await ctx.respond(
            (
                f"`{config_setting_name.replace("`", "\\`")}` "
                f"{
                    (
                        f"**=** {
                            "||" if CONFIG_SETTING_NEEDS_HIDING else ""
                        }`{
                            config_setting_value.replace("`", "\\`")
                        }`{
                            "||" if CONFIG_SETTING_NEEDS_HIDING else ""
                        }"
                    )
                    if config_setting_value
                    else "**is not set**."
                }"
            ),
            ephemeral=True,
        )
