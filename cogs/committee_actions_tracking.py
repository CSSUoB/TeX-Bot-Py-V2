"""Contains cog classes for tracking committee-actions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommitteeActionsTrackingCog",)

import logging
from logging import Logger

import discord
from asgiref.sync import sync_to_async
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError

from db.core.models import Action, DiscordMember
from exceptions.base import BaseDoesNotExistError
from utils import (
    CommandChecks,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)

logger: Logger = logging.getLogger("TeX-Bot")


class CommitteeActionsTrackingCog(TeXBotBaseCog):
    """Cog class that defines the committee-actions tracking functionality."""

    committee_actions: discord.SlashCommandGroup = discord.SlashCommandGroup(
        "committeeactions",
        "Add, list & remove tracked committee-actions.",
    )

    @staticmethod
    async def autocomplete_get_committee_members(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """Autocomplete callable that generates a set of selectable committee members."""
        shortcut_accessors_failed_error: BaseDoesNotExistError
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            committee_role: discord.Role = await ctx.bot.committee_role
        except BaseDoesNotExistError as shortcut_accessors_failed_error:
            logger.warning(shortcut_accessors_failed_error.message)
            return set()

        return {
            discord.OptionChoice(name=member.name, value=str(member.id))
            for member
            in main_guild.members
            if not member.bot and committee_role in member.roles
        }

    @classmethod
    async def action_autocomplete_get_all_actions(cls) -> set[discord.OptionChoice]:
        """
        Autocomplete callable that provides a set of selectable committee tracked-actions.

        Each action is identified by its description.
        """
        actions = await sync_to_async(Action.objects.all)()
        return {
            discord.OptionChoice(name=str(action.description), value=str(action)) # type: ignore[attr-defined]
            for action
            in actions
        }

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="action",
        description="Adds a new action with the specified description",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description of the action to assign.",
        input_type=str,
        required=True,
        parameter_name="str_action_description",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to action, if no user is specified, default to self",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_committee_members), # type: ignore[arg-type]
        required=True,
        parameter_name="str_action_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def action(self, ctx: TeXBotApplicationContext, str_action_member_id: str, str_action_description: str) -> None:  # noqa: E501
        """
        Definition and callback response of the "action" command.

        The action command adds an action to the specified user. If no user is specified
        we assume the action is aimed at the command issuer.
        """
        try:
            action: Action = await Action.objects.acreate(   # type: ignore[assignment]
                discord_id=int(str_action_member_id),
                description=str_action_description,
            )
        except ValidationError as create_action_error:
            error_is_already_exits: bool = (
                "__all__" in create_action_error.message_dict
                and any (
                    "already exists" in error
                    for error
                    in create_action_error.message_dict["__all__"]
                )
            )
            if not error_is_already_exits:
                await self.command_send_error(ctx, message="An unrecoverable error occured.")
                logger.critical(
                    "Error upon creating Action object: %s",
                    create_action_error,
                )
                await self.bot.close()
                return

            await self.command_send_error(
                ctx,
                message="You already have an action with that description!",
            )
            return

        await ctx.respond(f"Action: {action.description} created for user: <@{str_action_member_id}>")  # noqa: E501

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="list-user-actions",
        description="Lists all actions for a specified user",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to list actions for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_committee_members), # type: ignore[arg-type]
        required=True,
        parameter_name="str_action_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def list_user_actions(self, ctx:TeXBotApplicationContext, str_action_member_id: str) -> None:  # noqa: E501
        """
        Definition and callback of the list user actions command.

        Takes in a user and lists out their current actions.
        """
        action_member: discord.Member = await self.bot.get_member_from_str_id(str_action_member_id)  # noqa: E501

        if not action_member:
            await ctx.respond("The user you supplied doesn't exist or isn't in the server.")
            return

        user_actions = [action async for action in await Action.objects.afilter(
            discord_id=int(str_action_member_id),
        )]

        if not user_actions:
            await ctx.respond(f"User: {action_member.mention} has no actions.")
            logger.debug(user_actions)
        else:
            await ctx.respond(f"Found {len(user_actions)} actions for user {action_member.mention}:\n{"\n".join(str(action.description) for action in user_actions)}") # type: ignore[attr-defined]  # noqa: E501


    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="complete-action",
        description="Deletes the specified action as being completed.",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to mark as completed.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(action_autocomplete_get_all_actions), # type: ignore[arg-type]
        required=True,
        parameter_name="str_action_object",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def complete_action(self, ctx:TeXBotApplicationContext, str_action_object: str) -> None:  # noqa: E501
        """
        Definition and callback of the complete action command.

        Marks the specified action as complete by deleting it.
        """
        components = str_action_object.split(":")
        input_hashed_id = components[0].strip()
        input_description = components[1].strip()

        try:
            action = await Action.objects.aget(
                hashed_member_id=input_hashed_id,
                description=input_description,
            )
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await ctx.respond("Provided action was either not unique or did not exist.")
            logger.warning(
                "Action object: %s could not be matched to a unique action.",
                str_action_object,
            )

        await ctx.respond(f"Action: {action} found! Deleting.")
        await action.adelete()


    @discord.slash_command( # type: ignore[no-untyped-call, misc]
            name="reassign-action",
            description="Reassign the specified action to another user.",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to reassign.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(action_autocomplete_get_all_actions), # type: ignore[arg-type]
        required=True,
        parameter_name="str_action_object",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to list actions for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_committee_members), # type: ignore[arg-type]
        required=True,
        parameter_name="str_action_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def reassign_action(self, ctx:TeXBotApplicationContext, str_action_object: str, str_action_member_id: str) -> None:  # noqa: E501
        """Reassign the specified action to the specified user."""
        components = str_action_object.split(":")
        input_hashed_id = components[0].strip()
        input_description = components[1].strip()

        try:
            action_to_reassign = await Action.objects.aget(hashed_member_id=input_hashed_id, description=input_description)  # noqa: E501
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await ctx.respond("Provided action was either not unique or did not exist.")
            logger.warning("Action object: %s could not be matched to a unique action.", str_action_object)  # noqa: E501

        if input_hashed_id == DiscordMember.hash_discord_id(str_action_member_id):
            await ctx.respond(f"HEY! Action: {input_description} is already assigned to user: <@{str_action_member_id}>\nNo action has been taken.")  # noqa: E501
            return

        action_to_reassign.discord_member.hashed_discord_id = DiscordMember.hash_discord_id(str(str_action_member_id))  # noqa: E501

        await ctx.respond("Action successfully reassigned!")

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="list-all-actions",
        description="List all current actions.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def list_all_actions(self, ctx:TeXBotApplicationContext) -> None:
        """List all actions."""
        main_guild: discord.Guild = self.bot.main_guild
        committee_role: discord.Role = await self.bot.committee_role

        actions: list[Action] = list(await sync_to_async(Action.objects.all)())

        committee_members: set[discord.Member] = {member for member in main_guild.members if not member.bot and committee_role in member.roles}  # noqa: E501

        committee_actions: dict[discord.Member, list[Action]] = {committee: [action for action in actions if action.discord_member.hashed_discord_id == DiscordMember.hash_discord_id(committee.id)] for committee in committee_members}  # noqa: E501

        all_actions_message: str = "\n".join([f"Listing all actions by committee member:\n{committee.mention}, Actions:\n{', \n'.join(str(action.description) for action in actions)}" for committee, actions in committee_actions.items()])  # type: ignore[attr-defined]  # noqa: E501

        await ctx.respond(all_actions_message)
