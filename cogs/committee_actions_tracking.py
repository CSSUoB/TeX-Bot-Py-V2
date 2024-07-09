"""Contains cog classes for tracking committee-actions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommitteeActionsTrackingCog",)

import logging
import random
from logging import Logger

import discord
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

    @staticmethod
    async def action_autocomplete_get_all_actions(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501, ARG004
        """
        Autocomplete callable that provides a set of selectable committee tracked-actions.

        Each action is identified by its description.
        """
        all_actions: list[Action] = [action async for action in Action.objects.select_related().all()]  # noqa: E501

        if not all_actions:
            logger.debug("User tried to autocomplete for Actions but no actions were found!")
            return set()

        return {
            discord.OptionChoice(name=str(action.description), value=str(action))
            for action
            in all_actions
        }

    async def _create_action(self, ctx: TeXBotApplicationContext, action_user: discord.Member, description: str) -> Action | None:  # noqa: E501
        """Create the action object with the given description for the given user."""
        try:
            action: Action = await Action.objects.acreate(
                discord_id=int(action_user.id),
                description=description,
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
                return None

            await self.command_send_error(
                ctx,
                message=(
                    f"User: {action_user} already has an action "
                    f"with description: {description}!"
                ),
            )
            logger.debug(
                "Action creation for user: %s, failed because an action "
                "with description: %s, already exists.",
                action_user,
                description,
            )
            return None
        await ctx.respond(content=(
                f"Action: {action.description} created "
                f"for user: {action_user.mention}"
            ))
        return action


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

        The action command adds an action to the specified user.
        """
        action_user: discord.Member = await self.bot.get_member_from_str_id(str_action_member_id)  # noqa: E501

        if not action_user:
            await ctx.respond(content=(
                    f"The user you supplied, <@{str_action_member_id}> doesn't "
                    "exist or is not in the sever."
                ),
            )
            return

        await self._create_action(ctx, action_user, str_action_description)


    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="action-random-user",
        description="Creates an action object with the specified description and random user.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description to be used for the action",
        input_type=str,
        required=True,
        parameter_name="str_action_description",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def action_random_user(self, ctx: TeXBotApplicationContext, str_action_description: str) -> None:  # noqa: E501
        """
        Definition and callback response of the "action-random-user" command.

        Creates an action object with the specified description
        but randomises the committee member.
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_members: list[discord.Member] = committee_role.members

        if not committee_members:
            await ctx.respond(content=(
                "No committee members were found to randomly select from! Command aborted."
            ))
            return

        action_user: discord.Member = committee_members[random.randint(0, len(committee_members))]  # noqa: E501

        if not action_user:
            await ctx.respond(
                "Something went wrong and TeX-Bot was unable to randomly select someone.",
            )
            return

        await self._create_action(ctx, action_user, str_action_description)

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="action-all-committee",
        description="Creates an action with the description for every committee member",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description to be used for the actions",
        input_type=str,
        required=True,
        parameter_name="str_action_description",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def action_all_committee(self, ctx: TeXBotApplicationContext, str_action_description: str) -> None: # noqa: E501
        """
        Definition and callback response of the "action-all-committee" command.

        Creates an action object with the specified description for all committee members.
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_members: list[discord.Member] = committee_role.members

        if not committee_members:
            await ctx.respond(content="No committee members were found! Command aborted.")
            return

        committee_member: discord.Member
        for committee_member in committee_members:
            await self._create_action(ctx, committee_member, str_action_description)

        await ctx.respond(content="Done!")


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
            return

        await ctx.respond(f"Found {len(user_actions)} actions for user {action_member.mention}:\n{"\n".join(str(action.description) for action in user_actions)}")  # noqa: E501


    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="list-my-actions",
        description="Lists all actions for the user that ran the command",
    )
    @CommandChecks.check_interaction_user_in_main_guild
    async def list_my_actions(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition and callback of the list my actions command.

        Takes no arguments and simply returns the actions for the user that ran the command.
        """
        command_user: discord.Member = ctx.user

        user_actions: list[Action] = [action async for action in await Action.objects.afilter(
            discord_id=int(command_user.id),
        )]

        if not user_actions:
            await ctx.respond(content=":warning: You do not have any actions!")
            logger.debug(
                "User: %s ran the list-my-actions slash-command but no actions were found!",
            )
            return

        await ctx.respond(content=f"You have {len(user_actions)} actions: \n{"\n".join(str(action.description) for action in user_actions)}")  # noqa: E501


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
        input_description = components[1].strip()

        try:
            # NOTE: we only compare the description here because it is not possible, due to the hashing, to also check the discord user.
            action: Action = await Action.objects.select_related().aget(
                description=input_description,
            )
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await ctx.respond(
                ":warning: Provided action was either not unique or did not exist.",
            )
            logger.warning(
                "Action object: %s could not be matched to a unique action.",
                str_action_object,
            )

        if not action:
            logger.debug("Something went wrong and the action could not be retrieved.")
            ctx.respond("Something went wrong and the action could not be retrieved.")
            return

        await action.adelete()
        await ctx.respond(f"Action: {action.description} deleted!")
        logger.debug("Action: %s has been deleted.", action.description)


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

        logger.debug("Hashed input ID: %s", input_hashed_id)
        logger.debug("Input description: %s", input_description)

        try:
            action_to_reassign = await Action.objects.aget(
                discord_member_id=input_hashed_id, # NOTE: this shit broke fr fr
                description=input_description,
            )
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await ctx.respond("Provided action was either not unique or did not exist.")
            logger.warning("Action object: %s could not be matched to a unique action.", str_action_object)  # noqa: E501

        logger.debug("Found the action! %s", action_to_reassign)

        if input_hashed_id == DiscordMember.hash_discord_id(str_action_member_id):
            await ctx.respond(f"HEY! Action: {input_description} is already assigned to user: <@{str_action_member_id}>\nNo action has been taken.")  # noqa: E501
            return

        logger.debug("Action specified does not already belong to the user... proceeding.")

        action_to_reassign.discord_member = DiscordMember.hash_discord_id(str(str_action_member_id))  # type: ignore[has-type] # noqa: E501

        await ctx.respond("Action successfully reassigned!")

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="list-all-actions",
        description="List all current actions.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def list_all_actions(self, ctx:TeXBotApplicationContext) -> None:
        """List all actions."""
        committee_role: discord.Role = await self.bot.committee_role

        actions: list[Action] = [action async for action in Action.objects.select_related().all()]  # noqa: E501

        committee_members: list[discord.Member] = committee_role.members

        committee_actions: dict[discord.Member, list[Action]] = {committee: [action for action in actions if action.discord_member.hashed_discord_id == DiscordMember.hash_discord_id(committee.id)] for committee in committee_members} # type: ignore [has-type] # noqa: E501

        all_actions_message: str = "\n".join([f"\n{committee.mention}, Actions:\n{', \n'.join(str(action.description) for action in actions)}" for committee, actions in committee_actions.items()]) # noqa: E501

        await ctx.respond(all_actions_message)


    @discord.message_command( # type: ignore[no-untyped-call, misc]
        name="Action Message Author",
        description="Creates a new action for the message author using the message content.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def action_message_author(self, ctx: TeXBotApplicationContext, message: discord.Message) -> None:  # noqa: E501
        """
        Definition and callback response of the "action-message-author" message command.

        Creates a new action assigned to the message author
        using the message content as the description of the action.
        """
        if message.author.bot:
            await ctx.respond(content="Actions cannot be assigned to bots you melon!")
            logger.debug("User: %s, attempted to action a bot. silly billy.", ctx.user)
            return

        actioned_message_text: str = message.content
        actioned_message_user: discord.Member | discord.User = message.author

        if isinstance(actioned_message_user, discord.User):
            await ctx.respond("Message author is not in the server!")
            return

        await self._create_action(ctx, actioned_message_user, actioned_message_text)
