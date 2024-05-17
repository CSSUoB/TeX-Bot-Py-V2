"""Contains cog classes for tracking committee actions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("ActionsTrackingCog",)

import logging
from logging import Logger

import discord
from django.core.exceptions import ValidationError

from db.core.models import Action
from exceptions import CommitteeRoleDoesNotExistError, GuildDoesNotExistError
from utils import (
    CommandChecks,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)

logger: Logger = logging.getLogger("TeX-Bot")


class ActionsTrackingCog(TeXBotBaseCog):
    """Cog class that defines the action tracking functionality."""

    @staticmethod
    async def action_autocomplete_get_committee(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]: # noqa: E501
        """
        Autocomplete callable that generates a set of selectable committee members.

        This list is used to give a list of actionable committee members.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            committee_role: discord.Role = await ctx.bot.committee_role
        except (GuildDoesNotExistError, CommitteeRoleDoesNotExistError):
            logger.warning("Guild not found or committee role not found")
            return set()

        committee_members: set[discord.Member] = {member for member in main_guild.members if not member.bot and committee_role in member.roles}  # noqa: E501

        return {
            discord.OptionChoice(name=committee_member.name, value=str(committee_member.id))
            for committee_member
            in committee_members
        }

    async def action_autocomplete_get_all_actions(self) -> set[discord.OptionChoice]:
        """
        Autocomplete callable that generates a set of actions.

        Returns a list of actions that exist.
        """
        actions = [action async for action in Action.objects.all()]

        if not actions:
            return set()

        return {
            discord.OptionChoice(name=str(action.description), value=str(action))
            for action
            in actions
        }




    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="action",
        description="Adds a new action with the specified description",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description of the action to assign.",
        input_type=str,
        required=True,
        parameter_name="str_action_description",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to action, if no user is specified, default to self",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(action_autocomplete_get_committee), # type: ignore[arg-type]
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
            action: Action = await Action.objects.acreate(
                member_id=int(str_action_member_id),
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
        autocomplete=discord.utils.basic_autocomplete(action_autocomplete_get_committee), # type: ignore[arg-type]
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
        actions = [action async for action in Action.objects.all() if Action.hash_member_id(str_action_member_id) == action.hashed_member_id]  # noqa: E501
        action_member: discord.User | None = self.bot.get_user(int(str_action_member_id))

        if not action_member:
            await ctx.respond("The user you supplied doesn't exist or isn't in the server.")
            return

        if not actions:
            await ctx.respond(f"User: {action_member.mention} has no actions.")
        else:
            await ctx.respond(f"Found {len(actions)} actions for user {action_member.mention}:\n{"\n".join(str(action.description) for action in actions)}")  # noqa: E501


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
        actions = [action async for action in Action.objects.all()]

        components = str_action_object.split(":")
        hashed_id = components[0].strip()
        description = components[1].strip()

        action: Action
        for action in actions:
            if action.hashed_member_id == hashed_id and action.description == description:
                await ctx.respond(f"Found it chief! Action object: {action}")
                await action.adelete()
                return

        await ctx.respond("Hmm, I couldn't find that action. Please check the logs.")
        logger.error("Action: %s couldn't be deleted because it couldn't be found!")

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
        autocomplete=discord.utils.basic_autocomplete(action_autocomplete_get_committee), # type: ignore[arg-type]
        required=True,
        parameter_name="str_action_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def reassign_action(self, ctx:TeXBotApplicationContext, str_action_object: str, str_action_member_id: str) -> None:  # noqa: E501
        """Reassign the specified action to the specified user."""
        components = str_action_object.split(":")
        hashed_id = components[0].strip()
        description = components[1].strip()

        actions = [action async for action in Action.objects.all()]

        action_to_reassign: Action

        for action in actions:
            if action.hashed_member_id == hashed_id and action.description == description:
                action_to_reassign = action

        if not action_to_reassign:
            await ctx.respond("Something went wrong! Couldn't find that action...")
            logger.error(
                "Action: %s couldn't be reassigned because it couldn't be found!",
                str_action_object,
            )
            return

        if hashed_id == Action.hash_member_id(str_action_member_id):
            await ctx.respond(f"HEY! Action: {description} is already assigned to user: <@{str_action_member_id}>\nNo action has been taken.")  # noqa: E501
            return

        action_to_reassign.hashed_member_id = Action.hash_member_id(str_action_member_id)

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

        actions = [action async for action in Action.objects.all()]

        committee_members: set[discord.Member] = {member for member in main_guild.members if not member.bot and committee_role in member.roles}  # noqa: E501

        committee_actions = {committee: [action for action in actions if action.hashed_member_id == Action.hash_member_id(committee.id)] for committee in committee_members}  # noqa: E501

        all_actions_message = "\n".join([f"Listing all actions by committee member:\n{committee.mention}, Actions:\n{', \n'.join(str(action.description) for action in actions)}" for committee, actions in committee_actions.items()])  # noqa: E501

        await ctx.respond(all_actions_message)
