"""Contains cog classes for tracking committee-actions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommitteeActionsTrackingCog",)


import logging
import random
from logging import Logger
from typing import Final

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

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class CommitteeActionsTrackingCog(TeXBotBaseCog):
    """Cog class that defines the committee-actions tracking functionality."""

    committee_actions: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="committee-actions",
        description="Add, list, remove and reassign tracked committee-actions.",
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
    async def autocomplete_get_all_actions(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501, ARG004
        """
        Autocomplete callable that provides a set of selectable committee tracked-actions.

        Each action is identified by its description.
        """
        all_actions: list[Action] = [
            action async for action in Action.objects.select_related().all()
        ]

        if not all_actions:
            logger.debug("User tried to autocomplete for Actions but no actions were found!")
            return set()

        return {
            discord.OptionChoice(name=action.description, value=str(action.id))
            for action
            in all_actions
        }


    @staticmethod
    async def autocomplete_get_user_action_ids(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """Autocomplete callable that provides a set of actions that belong to the user."""
        if not ctx.interaction.user:
            logger.debug("User actions autocomplete did not have an interaction user!!")
            return set()

        interaction_user: discord.Member = await ctx.bot.get_member_from_str_id(
            str(ctx.interaction.user.id),
        )

        filtered_user_actions: list[Action] = [
            action async for action in await Action.objects.afilter(
                discord_id=int(interaction_user.id),
            )
        ]

        return {
            discord.OptionChoice(name=action.description, value=str(action.id))
            for action
            in filtered_user_actions
        }


    @staticmethod
    async def autocomplete_get_action_status(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501, ARG004
        """Autocomplete callable that provides the set of possible Status'of actions."""
        status_options: list[tuple[str, str]] = (
            Action._meta.get_field("status").__dict__["_choices"]
        )

        if not status_options:
            return set()

        return {
            discord.OptionChoice(name=value, value=code)
            for code, value
            in status_options
        }


    async def _create_action(self, ctx: TeXBotApplicationContext, action_user: discord.Member, description: str, *, silent: bool) -> Action | str:  # noqa: E501
        """
        Create the action object with the given description for the given user.

        If action creation is successful, the Action object will be returned.
        If unsuccessful, a string explaining the error will be returned.
        """
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
                return ""  # NOTE: this should never be called due to the close() call above, but is here just to be absolutely certain nothing else will be executed.

            DUPLICATE_ACTION_MESSAGE: Final[str] = (
                f"User: {action_user} already has an action "
                f"with description: {description}!"
            )
            if not silent:
                await self.command_send_error(
                    ctx,
                    message=(DUPLICATE_ACTION_MESSAGE),
                )
            logger.debug(
                "Action creation for user: %s, failed because an action "
                "with description: %s, already exists.",
                action_user,
                description,
            )
            return DUPLICATE_ACTION_MESSAGE
        if not silent:
            await ctx.respond(
                content=(
                    f"Action: {action.description} created "
                    f"for user: {action_user.mention}"
                ),
            )
        return action


    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="create",
        description="Adds a new action with the specified description",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to assign the action to",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_committee_members), # type: ignore[arg-type]
        required=True,
        parameter_name="str_action_member_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description of the action to assign.",
        input_type=str,
        required=True,
        parameter_name="action_description",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def create(self, ctx: TeXBotApplicationContext, str_action_member_id: str, action_description: str) -> None:  # noqa: E501
        """
        Definition and callback response of the "create" command.

        The "create" command creates an action assigned the specified user.
        """
        action_user: discord.Member = await self.bot.get_member_from_str_id(
            str_action_member_id,
        )

        await self._create_action(ctx, action_user, action_description, silent=False)

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="update-status",
        description="Update the status of the provided action.",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to mark as completed.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_user_action_ids), # type: ignore[arg-type]
        required=True,
        parameter_name="action_id",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="status",
        description="The desired status of the action.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_action_status), # type: ignore[arg-type]
        required=True,
        parameter_name="status",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def update_status(self, ctx: TeXBotApplicationContext, action_id: str, status: str) -> None:  # noqa: E501
        """
        Update the status of the given action to the given status.

        Takes in an action object and a Status string,
        sets the status of the provided action to be the provided status.
        """
        try:
            action: Action = await Action.objects.select_related().aget(id=action_id)
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await self.command_send_error(
                ctx,
                message="Action provided was either not unique or could not be found.",
            )
            return

        try:
            new_status: Action.Status = Action.Status(status)
        except KeyError as key_error:
            await self.command_send_error(ctx, message=f"Invalid Action Status: {key_error}")
            return

        action.status = new_status

        await action.asave()

        await ctx.respond(
            content=f"Updated action: {action.description} status to be: {action.status}",
        )


    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="action-random-user",
        description="Creates an action object with the specified description and random user.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description to be used for the action",
        input_type=str,
        required=True,
        parameter_name="action_description",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def action_random_user(self, ctx: TeXBotApplicationContext, action_description: str) -> None:  # noqa: E501
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

        action_user: discord.Member = committee_members[
            random.randint(0, len(committee_members))
        ]

        await self._create_action(ctx, action_user, action_description, silent=False)

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="action-all-committee",
        description="Creates an action with the description for every committee member",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description to be used for the actions",
        input_type=str,
        required=True,
        parameter_name="action_description",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def action_all_committee(self, ctx: TeXBotApplicationContext, action_description: str) -> None: # noqa: E501
        """
        Definition and callback response of the "action-all-committee" command.

        Creates an action object with the specified description for all committee members.
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_members: list[discord.Member] = committee_role.members

        if not committee_members:
            await ctx.respond(content="No committee members were found! Command aborted.")
            return

        success_members: list[discord.Member] = []
        failed_members: str = ""

        committee_member: discord.Member
        for committee_member in committee_members:
            action_or_error_message: Action | str = await self._create_action(
                ctx,
                committee_member,
                action_description,
                silent=True,
            )
            if isinstance(action_or_error_message, Action):
                success_members.append(committee_member)
            else:
                failed_members += action_or_error_message + "\n"

        response_message: str = ""

        if success_members:
            response_message += (
                f"Successfully created action: {action_description} for users: \n"
            )

            response_message += (
                "\n".join(f"{success_member.mention}" for success_member in success_members)
            )

            if len(failed_members) > 1:
                response_message += (
                    "\n\nThe following errors were also raised: \n" + failed_members
                )
        else:
            response_message += (
                "Could not create any actions! See errors below: \n"
            )

            response_message += failed_members


        await ctx.respond(content=response_message)


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
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="ping",
        description="Triggers whether the message pings users or not.",
        input_type=bool,
        default=False,
        required=False,
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def list_user_actions(self, ctx:TeXBotApplicationContext, str_action_member_id: str, *, ping: bool) -> None:  # noqa: E501
        """
        Definition and callback of the list user actions command.

        Takes in a user and lists out their current actions.
        """
        action_member: discord.Member = await self.bot.get_member_from_str_id(
            str_action_member_id,
        )

        user_actions = [action async for action in await Action.objects.afilter(
            discord_id=int(str_action_member_id),
        )]

        if not user_actions:
            await ctx.respond(content=(
                f"User: {action_member.mention if ping else action_member} has no actions.",
            ))
            logger.debug(user_actions)
            return

        await ctx.respond(content=(
            f"Found {len(user_actions)} actions for user "
            f"{action_member.mention if ping else action_member}:"
            f"\n{"\n".join(str(action.description) for action in user_actions)}",
        ))


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
            await ctx.respond(content=":warning: You do not have any actions!", ephemeral=True)
            logger.debug(
                "User: %s ran the list-my-actions slash-command but no actions were found!",
            )
            return

        await ctx.respond(
            content=(
                f"You have {len(user_actions)} actions: "
                f"\n{"\n".join(str(action.description) + f" ({Action.Status(action.status).label})"
                for action in user_actions)}"  # noqa: E501
            ),
            ephemeral=True,
        )


    @discord.slash_command( # type: ignore[no-untyped-call, misc]
            name="reassign-action",
            description="Reassign the specified action to another user.",
    )
    @discord.option( # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to reassign.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_all_actions), # type: ignore[arg-type]
        required=True,
        parameter_name="action_id",
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
    async def reassign_action(self, ctx:TeXBotApplicationContext, action_id: str, str_action_member_id: str) -> None:  # noqa: E501
        """Reassign the specified action to the specified user."""
        new_user_to_action: discord.Member = await self.bot.get_member_from_str_id(
            str_action_member_id,
        )
        new_user_to_action_hash: str = DiscordMember.hash_discord_id(new_user_to_action.id)

        try:
            action_to_reassign: Action = (
                await Action.objects.select_related().aget(id=action_id)
            )
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await self.command_send_error(
                ctx,
                message="Action provided was either not unique or could not be found.",
            )
            return

        if str(action_to_reassign.discord_member) == new_user_to_action_hash: # type: ignore[has-type]
            await ctx.respond(
                content=(
                    f"HEY! Action: {action_to_reassign.description} is already assigned "
                    f"to user: {new_user_to_action.mention}\nNo action has been taken."
                ),
            )
            return

        new_action: Action | str = await self._create_action(
            ctx,
            new_user_to_action,
            action_to_reassign.description,
            silent=False,
        )

        if isinstance(new_action, Action):
            await action_to_reassign.adelete()


    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="list-all-actions",
        description="List all current actions.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="ping",
        description="Triggers whether the message pings users or not.",
        input_type=bool,
        default=False,
        required=False,
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def list_all_actions(self, ctx:TeXBotApplicationContext, *, ping: bool) -> None:
        """List all actions.""" # NOTE: this doesn't actually list *all* actions as it is possible for non-committee to be actioned.
        committee_role: discord.Role = await self.bot.committee_role

        actions: list[Action] = [
            action async for action in Action.objects.select_related().all()
        ]

        committee_members: list[discord.Member] = committee_role.members

        committee_actions: dict[discord.Member, list[Action]] = {
            committee: [
                action for action in actions
                if str(action.discord_member) == DiscordMember.hash_discord_id(committee.id) # type: ignore[has-type]
                and action.status != "X" and action.status != "C"
            ] for committee in committee_members
        }

        filtered_committee_actions = {
            committee: actions for committee, actions in committee_actions.items() if actions
        }

        if not filtered_committee_actions:
            await ctx.respond(content="No one has any actions!")
            return

        all_actions_message: str = "\n".join([
                f"\n{committee.mention if ping else committee}, Actions:"
                f"\n{', \n'.join(str(action.description) + f"({Action.Status(action.status).label})" for action in actions)}"  # noqa: E501
                for committee, actions in filtered_committee_actions.items()
            ],
        )

        await ctx.respond(content=all_actions_message)


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
            await ctx.respond(content="Message author is not in the server!")
            return

        await self._create_action(
            ctx,
            actioned_message_user,
            actioned_message_text,
            silent=False,
        )
