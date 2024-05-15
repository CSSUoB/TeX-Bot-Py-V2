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
    async def list_user_actions(self, ctx:TeXBotApplicationContext, str_action_member_id: str) -> None:  # noqa: E501
        """
        Definition and callback of the list user actions command.

        Takes in a user and lists out their current actions.
        """
        actions = [action async for action in Action.objects.all() if Action.hash_member_id(str_action_member_id) == action.hashed_member_id]  # noqa: E501
        action_member: discord.User | None = self.bot.get_user(int(str_action_member_id))

        if not action_member:
            await ctx.respond("The user you supplied was dog shit. Fuck off cunt.")
            return

        if not actions:
            await ctx.respond(f"User: {action_member.mention} has no actions.")
        else:
            await ctx.respond(f"Found {len(actions)} actions for user {action_member.mention}:\n{"\n".join(str(action.description) for action in actions)}")  # noqa: E501






