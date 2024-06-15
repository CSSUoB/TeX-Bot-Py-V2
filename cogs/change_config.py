"""Contains cog classes for any config changing interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("ConfigChangeCommandsCog",)


import contextlib
import itertools
import logging
import random
import re
import urllib.parse
from collections.abc import MutableSequence, Set
from logging import Logger
from typing import Final

import discord
from discord.ui import View
from strictyaml import StrictYAMLError

import config
from config import CONFIG_SETTINGS_HELPS, ConfigSettingHelp, LogLevels
from config.constants import MESSAGES_LOCALE_CODES, SendIntroductionRemindersFlagType
from exceptions import (
    ChangingSettingWithRequiredSiblingError,
    CommitteeRoleDoesNotExistError,
    DiscordMemberNotInMainGuildError,
)
from exceptions.base import BaseDoesNotExistError
from utils import (
    CommandChecks,
    EditorResponseComponent,
    GenericResponderComponent,
    SenderResponseComponent,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class ConfirmSetConfigSettingValueView(View):
    """A discord.View containing two buttons to confirm setting a given config setting."""

    @discord.ui.button(  # type: ignore[misc]
        label="Yes",
        style=discord.ButtonStyle.red,
        custom_id="set_config_confirm",
    )
    async def confirm_set_config_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the yes button is pressed, delete the message."""
        logger.debug("\"Yes\" button pressed. %s", interaction)

    @discord.ui.button(  # type: ignore[misc]
        label="No",
        style=discord.ButtonStyle.green,
        custom_id="set_config_cancel",
    )
    async def cancel_set_config_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the no button is pressed, delete the message."""
        logger.debug("\"No\" button pressed. %s", interaction)


class ConfigChangeCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/config" command group and command call-back methods."""

    change_config: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="config",
        description="Display, edit and get help about TeX-Bot's configuration.",
    )

    @staticmethod
    async def autocomplete_get_settings_names(ctx: TeXBotAutocompleteContext) -> Set[discord.OptionChoice] | Set[str]:  # noqa: E501
        """Autocomplete callable that generates the set of available settings names."""
        if not ctx.interaction.user:
            return set()

        try:
            if not await ctx.bot.check_user_has_committee_role(ctx.interaction.user):
                return set()
        except (BaseDoesNotExistError, DiscordMemberNotInMainGuildError):
            return set()

        return set(config.CONFIG_SETTINGS_HELPS)

    @staticmethod
    async def autocomplete_get_example_setting_values(ctx: TeXBotAutocompleteContext) -> Set[discord.OptionChoice] | Set[str]:  # noqa: C901,PLR0911,PLR0912,E501
        """Autocomplete callable that generates example values for a configuration setting."""
        HAS_CONTEXT: Final[bool] = bool(
            ctx.interaction.user and "setting" in ctx.options and ctx.options["setting"],
        )
        if not HAS_CONTEXT:
            return set()

        try:
            if not await ctx.bot.check_user_has_committee_role(ctx.interaction.user):  # type: ignore[arg-type]
                return set()
        except (BaseDoesNotExistError, DiscordMemberNotInMainGuildError):
            return set()

        setting_name: str = ctx.options["setting"]

        if "token" in setting_name or "cookie" in setting_name or "secret" in setting_name:
            return set()

        if ":log-level" in setting_name:
            return {log_level.value for log_level in LogLevels}

        if "discord" in setting_name and ":webhook-url" in setting_name:
            return {"https://discord.com/api/webhooks/"}

        if "members-list:id-format" in setting_name:
            return (
                {r"\A[a-z0-9]{" + str(2 ** id_length) + r"}\Z" for id_length in range(2, 9)}
                | {r"\A[A-F0-9]{" + str(2 ** id_length) + r"}\Z" for id_length in range(2, 9)}
                | {r"\A[0-9]{" + str(2 ** id_length) + r"}\Z" for id_length in range(2, 9)}
            )

        if "probability" in setting_name:
            return {
                "0",
                "0.01",
                "0.025",
                "0.05",
                "0.1",
                "0.125",
                "0.15",
                "0.20",
                "0.25",
                "0.4",
                "0.45",
                "0.5",
                "0.6",
                "0.65",
                "0.7",
                "0.75",
                "0.8",
                "0.85",
                "0.9",
                "0.95",
                "0.975",
                "0.99",
                "0.999",
                "1",
            }

        if ":lookback-days" in setting_name:
            return {
                "5",
                "7",
                "10",
                "20",
                "25",
                "27",
                "28",
                "30",
                "31",
                "50",
                "75",
                "100",
                "150",
                "200",
                "250",
                "500",
                "750",
                "1000",
                "1250",
                "1500",
                "1826",
            }

        if ":displayed-roles" in setting_name:
            return {
                "Committee,Member,Guest",
                (
                    "Foundation Year,First Year,Second Year,Final Year,Year In Industry,"
                    "Year Abroad,PGT,PGR,Alumnus/Alumna,Postdoc"
                ),
            }

        if "locale-code" in setting_name:
            return MESSAGES_LOCALE_CODES

        if "send-introduction-reminders:enable" in setting_name:
            return {
                str(flag_value).lower()
                for flag_value
                in getattr(SendIntroductionRemindersFlagType, "__args__")  # noqa: B009
            }

        if "send-get-roles-reminders:enable" in setting_name:
            return {"true", "false"}

        SETTING_NAME_IS_TIMEDELTA: Final[bool] = (
            ":timeout-duration" in setting_name
            or ":delay" in setting_name
            or ":interval" in setting_name
        )
        if SETTING_NAME_IS_TIMEDELTA:
            timedelta_scales: MutableSequence[str] = ["s", "m", "h"]

            if ":timeout-duration" in setting_name or ":delay" in setting_name:
                timedelta_scales.extend(["d", "w"])

            return {
                "".join(
                    (
                        (
                            f"{
                                (
                                    f"{
                                        str(
                                            random.choice(
                                                (
                                                    random.randint(1, 110),
                                                    round(
                                                        random.random() * 110,
                                                        random.randint(1, 3),
                                                    ),
                                                ),
                                            ),
                                        ).removesuffix(".0").removesuffix(".00").removesuffix(
                                            ".000",
                                        )
                                    }{
                                        selected_timedelta_scale
                                    }"
                                )
                                if selected_timedelta_scale
                                else ""
                            }"
                        )
                        for selected_timedelta_scale
                        in selected_timedelta_scales
                    ),
                )
                for _
                in range(4)
                for selected_timedelta_scales
                in itertools.product(
                    *(("", timedelta_scale) for timedelta_scale in timedelta_scales),
                )
                if any(selected_timedelta_scales)
            }

        if setting_name.endswith(":url") or re.search(r":links:[^:]+\Z", setting_name):
            if "purchase-membership" in setting_name or "membership-perks" in setting_name:
                return {
                    "https://",
                    "https://www.guildofstudents.com/studentgroups/societies/",
                    "https://www.guildofstudents.com/organisation/",
                }

            if "document" in setting_name:
                return {
                    "https://",
                    "https://drive.google.com/file/d/",
                    "https://docs.google.com/document/d/",
                    "https://onedrive.live.com/edit.aspx?resid=",
                    "https://1drv.ms/p/",
                } | {
                    f"https://{domain}.com/{path}"
                    for domain, path
                    in itertools.product(
                        ("github", "raw.githubusercontent"),
                        (f"{urllib.parse.quote(ctx.bot.group_short_name)}/", ""),
                    )
                } | {
                    f"https://{subdomain}dropbox{domain_suffix}.com/{path}"
                    for subdomain, domain_suffix, path
                    in itertools.product(
                        ("dl.", ""),
                        ("usercontent", ""),
                        ("shared/", "", "s/", "scl/fi/"),
                    )
                }

            return {"https://"}

        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except (BaseDoesNotExistError, DiscordMemberNotInMainGuildError):
            return set()

        if "community" in setting_name:
            SIMPLIFIED_FULL_NAME: Final[str] = (
                main_guild.name.strip().removeprefix("the").removeprefix("The").strip()
            )

            if ":full-name" in setting_name:
                return {
                    main_guild.name.strip(),
                    main_guild.name.strip().title(),
                    SIMPLIFIED_FULL_NAME.split()[0].rsplit("'")[0],
                    SIMPLIFIED_FULL_NAME.split()[0].rsplit("'")[0].capitalize(),
                }

            if ":short-name" in setting_name:
                return {
                    "".join(word[0].upper() for word in SIMPLIFIED_FULL_NAME.split()),
                    "".join(word[0].lower() for word in SIMPLIFIED_FULL_NAME.split()),
                }

        try:
            interaction_member: discord.Member = await ctx.bot.get_main_guild_member(
                ctx.interaction.user,  # type: ignore[arg-type]
            )
        except (BaseDoesNotExistError, DiscordMemberNotInMainGuildError):
            return set()

        if ":performed-manually-warning-location" in setting_name:
            return (
                {"DM"}
                | {
                    channel.name
                    for channel
                    in main_guild.text_channels
                    if channel.permissions_for(interaction_member).is_superset(
                        discord.Permissions(send_messages=True),
                    )
                }
            )

        return set()

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
                        else f"**is not set**.{
                            f"\nThe default value is `{
                                CONFIG_SETTINGS_HELPS[config_setting_name].default.replace(  # type: ignore[union-attr]
                                    "`",
                                    "\\`",
                                )
                            }`"
                            if CONFIG_SETTINGS_HELPS[config_setting_name].default is not None
                            else ""
                        }"
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

        SELECTED_SETTING_HAS_DEFAULT: Final[bool] = (
            config.CONFIG_SETTINGS_HELPS[config_setting_name].default is not None
        )

        if not SELECTED_SETTING_HAS_DEFAULT:
            response: discord.Message | discord.Interaction = await ctx.respond(
                content=(
                    f"Setting {config_setting_name.replace("`", "\\`")} "
                    "has no default value."
                    "If you overwrite it with a new value the old one will be lost "
                    "and cannot be restored.\n"
                    "Are you sure you want to overwrite the old value?\n\n"
                    "Please confirm using the buttons below."
                ),
                view=ConfirmSetConfigSettingValueView(),
                ephemeral=True,
            )

            committee_role: discord.Role | None = None
            with contextlib.suppress(CommitteeRoleDoesNotExistError):
                committee_role = await self.bot.committee_role

            confirmation_message: discord.Message = (
                response
                if isinstance(response, discord.Message)
                else await response.original_response()
            )
            button_interaction: discord.Interaction = await self.bot.wait_for(
                "interaction",
                check=lambda interaction: (
                    interaction.type == discord.InteractionType.component
                    and interaction.message.id == confirmation_message.id
                    and (
                        (committee_role in interaction.user.roles)
                        if committee_role
                        else True
                    )
                    and "custom_id" in interaction.data
                    and interaction.data["custom_id"] in {
                        "shutdown_confirm",
                        "shutdown_cancel",
                    }
                ),
            )

            if button_interaction.data["custom_id"] == "set_config_cancel":  # type: ignore[index, typeddict-item]
                await confirmation_message.edit(
                    content=(
                        "Aborting editing config setting: "
                        f"{config_setting_name.replace("`", "\\`")}"
                    ),
                    view=None,
                )
                return

            if button_interaction.data["custom_id"] != "set_config_confirm":  # type: ignore[index, typeddict-item]
                raise ValueError

        previous_config_setting_value: str | None = config.view_single_config_setting_value(
            config_setting_name,
        )

        responder: GenericResponderComponent = (
            EditorResponseComponent(ctx.interaction)
            if not SELECTED_SETTING_HAS_DEFAULT
            else SenderResponseComponent(ctx.interaction, ephemeral=True)
        )

        yaml_error: StrictYAMLError
        changing_setting_error: ChangingSettingWithRequiredSiblingError
        try:
            await config.assign_single_config_setting_value(
                config_setting_name,
                new_config_value,
            )

        except StrictYAMLError as yaml_error:
            if str(yaml_error) != yaml_error.context:
                INCONCLUSIVE_YAML_ERROR_MESSAGE: Final[str] = (
                    "Could not determine the error message from invalid YAML validation."
                )
                raise NotImplementedError(INCONCLUSIVE_YAML_ERROR_MESSAGE) from None

            await self.command_send_error(
                ctx,
                message=(
                    f"Changing setting value failed: "
                    f"{str(yaml_error.context)[0].upper()}"
                    f"{str(yaml_error.context)[1:].strip(" .")}."
                ),
                responder_component=responder,
            )
            return

        except ChangingSettingWithRequiredSiblingError as changing_setting_error:
            await self.command_send_error(
                ctx,
                message=(
                    f"{changing_setting_error} "
                    f"It will be easier to make your changes "
                    f"directly within the \"tex-bot-deployment.yaml\" file."
                ),
                responder_component=responder,
            )
            return

        changed_config_setting_value: str | None = config.view_single_config_setting_value(
            config_setting_name,
        )

        if changed_config_setting_value == previous_config_setting_value:
            await responder.respond(
                "No changes made. Provided value was the same as the previous value.",
                view=None,
            )
            return

        if isinstance(changed_config_setting_value, str):
            changed_config_setting_value = changed_config_setting_value.strip()

        CONFIG_SETTING_IS_SECRET: Final[bool] = bool(
            "token" in config_setting_name
            or "cookie" in config_setting_name
            or "secret" in config_setting_name  # noqa: COM812
        )
        await responder.respond(
            content=(
                f"Successfully updated setting: `{
                    config_setting_name.replace("`", "\\`")
                }`"
                f"{
                    "" if CONFIG_SETTING_IS_SECRET else (
                        (
                            f"**=** `{
                                changed_config_setting_value.replace("`", "\\`")
                            }`"
                        )
                        if changed_config_setting_value
                        else "**to be not set**."
                    )
                }\n\n"
                "Changes could take up to ??? to take effect."  # TODO: Retrieve update time from task
            ),
            view=None,
        )

    # TODO: Command to unset value (if it is optional)
