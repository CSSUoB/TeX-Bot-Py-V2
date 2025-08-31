"""Contains cog classes for tracking committee-actions."""

import contextlib
import datetime
import logging
import random
import time
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, overload, override, cast

import discord
from discord.ext import tasks
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db.models import Q

from config import settings
from db.core.models import AssignedCommitteeAction, DiscordMember
from exceptions import (
    CommitteeElectRoleDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    InvalidActionDescriptionError,
    InvalidActionTargetError,
)
from utils import CommandChecks, TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBot, TeXBotApplicationContext, TeXBotAutocompleteContext

__all__: "Sequence[str]" = (
    "CommitteeActionsTrackingBaseCog",
    "CommitteeActionsTrackingContextCommandsCog",
    "CommitteeActionsTrackingRemindersTaskCog",
    "CommitteeActionsTrackingSlashCommandsCog",
)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class CommitteeActionsTrackingBaseCog(TeXBotBaseCog):
    """Base cog class that defines methods for committee actions tracking."""

    async def _get_all_actions(self) -> dict[str, list[AssignedCommitteeAction]]:
        grouped_actions: dict[str, list[AssignedCommitteeAction]] = defaultdict(list)

        action: AssignedCommitteeAction
        async for action in AssignedCommitteeAction.objects.select_related(
            "discord_member"
        ).all():
            grouped_actions[action.discord_member.discord_id].append(action)

        return grouped_actions

    async def _get_incomplete_actions(self) -> dict[str, list[AssignedCommitteeAction]]:
        """Get a list of all actions that are in progress."""
        grouped_filtered_actions: dict[str, list[AssignedCommitteeAction]] = defaultdict(list)

        async for action in AssignedCommitteeAction.objects.select_related(
            "discord_member"
        ).filter(
            Q(status=AssignedCommitteeAction.Status.IN_PROGRESS.value)
            | Q(status=AssignedCommitteeAction.Status.BLOCKED.value)
            | Q(status=AssignedCommitteeAction.Status.NOT_STARTED.value)
        ):
            grouped_filtered_actions[action.discord_member.discord_id].append(action)

        return grouped_filtered_actions

    async def _update_action_board(self) -> None:
        """
        Update the action board message with the current actions.

        This method should be called after any action is created, updated or deleted.
        """
        if not settings["COMMITTEE_ACTIONS_BOARD"]:
            return

        action_board_channel: discord.TextChannel | None = discord.utils.get(
            self.bot.main_guild.text_channels,
            name=settings["COMMITTEE_ACTIONS_BOARD_CHANNEL"],
        )

        if not action_board_channel:
            logger.warning(
                "Action board channel could not be found so "
                "the action board will not be updated."
            )
            return

        action_board_message: discord.Message | None = await action_board_channel.history(
            limit=1
        ).next()

        if not action_board_message or action_board_message.author != self.bot.user:
            action_board_message = await action_board_channel.send(
                content="**Committee Actions Tracking Board**\n"
            )

        all_actions: dict[
            str, list[AssignedCommitteeAction]
        ] = await self._get_incomplete_actions()

        if not all_actions:
            return

        all_actions_message: str = "\n".join(
            [
                f"\n<@{discord_id}>, Actions:"
                f"\n{
                    ', \n'.join(
                        action.status.emoji + ' ' + f'{action.description} ' + f'({action.status})'
                        for action in actions
                    )
                }"
                for discord_id, actions in all_actions.items()
            ],
        )

        await action_board_message.edit(
            content=(f"## Committee Actions Tracking Board\n{all_actions_message}"),
        )

    async def _create_action(
        self, ctx: "TeXBotApplicationContext", action_user: discord.Member, description: str
    ) -> AssignedCommitteeAction | None:
        """
        Create the action object with the given description for the given user.

        If action creation is successful, the Action object will be returned.
        If unsuccessful, a string explaining the error will be returned.
        """
        if len(description) >= 200:
            INVALID_DESCRIPTION_ERROR_MESSAGE: Final[str] = (
                f"Action description length was {len(description)} characters which is "
                "greater than the maximum of 200."
            )
            raise InvalidActionTargetError(message=INVALID_DESCRIPTION_ERROR_MESSAGE)

        if action_user.bot:
            INVALID_ACTION_TARGET_MESSAGE: Final[str] = (
                f"Actions cannot be assigned to bots. ({action_user})"
            )
            raise InvalidActionTargetError(message=INVALID_ACTION_TARGET_MESSAGE)

        try:
            action: AssignedCommitteeAction = await AssignedCommitteeAction.objects.acreate(
                discord_member=(
                    await DiscordMember.objects.aget_or_create(discord_id=action_user.id)
                )[0],
                description=description,
            )
        except ValidationError as create_action_error:
            error_is_already_exits: bool = (
                "__all__" in create_action_error.message_dict
                and any(
                    "already exists" in error
                    for error in create_action_error.message_dict["__all__"]
                )
            )
            if not error_is_already_exits:
                await self.command_send_error(ctx, message="An unrecoverable error occured.")
                logger.critical("Error upon creating Action object: %s", create_action_error)
                await self.bot.close()

            DUPLICATE_ACTION_MESSAGE: Final[str] = (
                f"User: {action_user} already has an action with description: {description}!"
            )
            logger.debug(
                (
                    "Action creation for user: %s, failed because an action "
                    "with description: %s, already exists."
                ),
                action_user,
                description,
            )
            raise InvalidActionDescriptionError(
                message=DUPLICATE_ACTION_MESSAGE
            ) from create_action_error
        await self._update_action_board()
        return action

    @overload
    @staticmethod
    async def get_user_actions(
        action_user: discord.Member | discord.User, status: list[str]
    ) -> list[AssignedCommitteeAction]: ...

    @overload
    @staticmethod
    async def get_user_actions(
        action_user: "Iterable[discord.Member]",
        status: list[str],
    ) -> dict[discord.Member, list[AssignedCommitteeAction]]: ...

    @staticmethod
    async def get_user_actions(
        action_user: "discord.Member | discord.User | Iterable[discord.Member]",
        status: str | list[str],
    ) -> list[AssignedCommitteeAction] | dict[discord.Member, list[AssignedCommitteeAction]]:
        """
        Get the actions for a given user.

        Takes in the user and returns a list of their actions.
        """
        if isinstance(action_user, (discord.User, discord.Member)):
            user_actions: list[AssignedCommitteeAction] = [
                action
                async for action in AssignedCommitteeAction.objects.filter(
                    status=status,
                    discord_member__discord_id=int(action_user.id),
                )
            ]

            return user_actions

        actions: list[AssignedCommitteeAction] = [
            action async for action in AssignedCommitteeAction.objects.select_related().all()
        ]

        committee_actions: dict[discord.Member, list[AssignedCommitteeAction]] = {
            committee: [
                action
                for action in actions
                if str(action.discord_member.discord_id) == str(committee.id)
                and action.status in status
            ]
            for committee in action_user
        }

        return {
            committee: actions for committee, actions in committee_actions.items() if actions
        }


class CommitteeActionsTrackingRemindersTaskCog(CommitteeActionsTrackingBaseCog):
    """Cog class that defines the committee-actions tracking reminders task functionality."""

    @override
    def __init__(self, bot: "TeXBot") -> None:
        """Start all task managers when this cog is initialised."""
        if settings["SEND_COMMITTEE_ACTIONS_REMINDERS"]:
            _ = self.send_committee_actions_reminders_task.start()

        super().__init__(bot)

    @override
    def cog_unload(self) -> None:
        """
        Unload-hook that ends all running tasks whenever the tasks cog is unloaded.

        This may be run dynamically or when the bot closes.
        """
        self.send_committee_actions_reminders_task.cancel()

    @tasks.loop(**settings["COMMITTEE_ACTIONS_REMINDERS_INTERVAL"])
    @capture_guild_does_not_exist_error
    async def send_committee_actions_reminders_task(self) -> None:
        """
        Definition of the background task that sends reminders of committee actions.

        The task will run every interval specified in the settings and will send reminders
        to all committee members who have actions that are either in progress or not started.
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_action_reminders_channel: discord.TextChannel | None = discord.utils.get(
            self.bot.main_guild.text_channels,
            name=settings["COMMITTEE_ACTIONS_REMINDERS_CHANNEL"],
        )

        if not committee_action_reminders_channel:
            logger.warning(
                "Committee actions reminders channel could not be found! "
                "Actions reminders task will not run until next restart."
            )
            self.send_committee_actions_reminders_task.cancel()
            return

        all_actions: dict[
            discord.Member, list[AssignedCommitteeAction]
        ] = await self.get_user_actions(
            action_user=committee_role.members,
            status=[Status.NOT_STARTED.value, Status.IN_PROGRESS.value, Status.BLOCKED.value],
        )

        interval_seconds: float = datetime.timedelta(
            **settings["COMMITTEE_ACTIONS_REMINDERS_INTERVAL"]
        ).total_seconds()
        next_reminder_unix = int(time.time() + interval_seconds)

        actions_reminder_info_message: str = (
            f"Wakey wakey committee!\n"
            "Here are your actions that are either in progress or not started yet.\n"
            f"I'll remind you again <t:{next_reminder_unix}:R>"
        )

        all_actions_message: str = "\n".join(
            [
                f"\n{committee}, Actions:"
                f"\n{
                    ', \n'.join(
                        action.status.emoji + ' ' + f'{action.description} ' + f'({action.status})'
                        for action in actions
                    )
                }"
                for committee, actions in all_actions.items()
            ],
        )

        if not all_actions_message:
            logger.info("No actions found for any committee members. No reminders sent.")
            return

        await committee_action_reminders_channel.send(
            content=f"{actions_reminder_info_message}\n{all_actions_message}",
        )

    @send_committee_actions_reminders_task.before_loop
    async def before_tasks(self) -> None:
        """Pre-execution hook, preventing any tasks from executing before the bot is ready."""
        await self.bot.wait_until_ready()


class CommitteeActionsTrackingSlashCommandsCog(CommitteeActionsTrackingBaseCog):
    """Cog class that defines the committee-actions tracking slash commands functionality."""

    committee_actions: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="committee-actions",
        description="Add, list, remove and reassign tracked committee-actions.",
    )

    @staticmethod
    async def autocomplete_get_committee_members(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete callable that generates a set of selectable committee members."""
        try:
            committee_role: discord.Role = await ctx.bot.committee_role
        except CommitteeRoleDoesNotExistError:
            return set()

        committee_elect_role: discord.Role | None = None
        with contextlib.suppress(CommitteeElectRoleDoesNotExistError):
            committee_elect_role = await ctx.bot.committee_elect_role

        return {
            discord.OptionChoice(
                name=f"{member.display_name} ({member.global_name})", value=str(member.id)
            )
            for member in (
                set(committee_role.members)
                | (
                    set(committee_elect_role.members)
                    if committee_elect_role is not None
                    else set()
                )
            )
            if not member.bot
        }

    @staticmethod
    async def autocomplete_get_user_action_ids(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete callable that provides a set of actions that belong to the user."""
        if not ctx.interaction.user:
            logger.debug("User actions autocomplete did not have an interaction user!!")
            return set()

        try:
            interaction_user: discord.Member = await ctx.bot.get_member_from_str_id(
                str(ctx.interaction.user.id)
            )
        except ValueError:
            logger.debug("User action ID autocomplete could not acquire an interaction user!")
            return set()

        admin_role: discord.Role | None = discord.utils.get(
            ctx.bot.main_guild.roles, name="Admin"
        )

        if admin_role and admin_role in interaction_user.roles:
            return {
                discord.OptionChoice(
                    name=f"{action.description} ({action.status})", value=str(action.id)
                )
                async for action in AssignedCommitteeAction.objects.select_related().all()
            }

        return {
            discord.OptionChoice(name=action.description, value=str(action.id))
            async for action in AssignedCommitteeAction.objects.filter(
                (
                    Q(status=AssignedCommitteeAction.Status.IN_PROGRESS.value)
                    | Q(status=AssignedCommitteeAction.Status.BLOCKED.value)
                    | Q(status=AssignedCommitteeAction.Status.NOT_STARTED.value)
                ),
                discord_member__discord_id=interaction_user.id,
            )
        }

    @staticmethod
    async def autocomplete_get_action_status(
        ctx: "TeXBotAutocompleteContext",  # noqa: ARG004
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete callable that provides the set of possible Status' of actions."""
        status_options: Sequence[tuple[str, str]] = AssignedCommitteeAction._meta.get_field(
            "status"
        ).choices  # type: ignore[assignment]

        if not status_options:
            logger.error("The autocomplete could not find any action Status'!")
            return set()

        return {discord.OptionChoice(name=value, value=code) for code, value in status_options}

    @committee_actions.command(
        name="create", description="Adds a new action with the specified description."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description of the action to assign.",
        input_type=str,
        required=True,
        parameter_name="action_description",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to assign the action to.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_committee_members),  # type: ignore[arg-type]
        required=False,
        default=None,
        parameter_name="action_member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def create(
        self,
        ctx: "TeXBotApplicationContext",
        action_description: str,
        action_member_id: str | None,
    ) -> None:
        """
        Definition and callback response of the "create" command.

        The "create" command creates an action with the specified description.
        If no user is specified, the user issuing the command will be actioned.
        In normal use the autocomplete should be used, but a discord ID can be
        used directly if the user wishes to action a user not included in the autocomplete.
        """
        member_id: str = action_member_id if action_member_id else str(ctx.user.id)

        try:
            action_user: discord.Member = await self.bot.get_member_from_str_id(member_id)
        except ValueError:
            await ctx.respond(
                content=f":warning: The user ID provided: {member_id}, was not valid.",
                ephemeral=True,
            )
            logger.debug(
                "User: %s, tried to create an action with an invalid user ID: %s",
                ctx.user,
                member_id,
            )
            return

        try:
            await self._create_action(ctx, action_user, action_description)
            await ctx.respond(
                content=f"Action `{action_description}` created for: {action_user.mention}"
            )
        except (
            InvalidActionDescriptionError,
            InvalidActionTargetError,
        ) as creation_failed_error:
            await ctx.respond(content=creation_failed_error.message)

    @committee_actions.command(
        name="update-status", description="Update the status of the provided action."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to mark as completed.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_user_action_ids),  # type: ignore[arg-type]
        required=True,
        parameter_name="action_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="status",
        description="The desired status of the action.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_action_status),  # type: ignore[arg-type]
        required=True,
        parameter_name="status",
    )
    async def update_status(  # NOTE: Committee role check is not present because non-committee can have actions, and need to be able to list their own actions.
        self, ctx: "TeXBotApplicationContext", action_id: str, status: str
    ) -> None:
        """
        Definition and callback of the "update-status" command.

        Takes in an action object and a Status string,
        sets the status of the provided action to be the provided status.
        """
        try:
            action_id_int: int = int(action_id)
        except ValueError:
            await self.command_send_error(
                ctx,
                message="Action ID entered was not valid! Please use the autocomplete.",
                logging_message=f"{ctx.user} entered action ID: {action_id} which was invalid",
            )
            return

        try:
            action: AssignedCommitteeAction = (
                await AssignedCommitteeAction.objects.select_related().aget(id=action_id_int)
            )
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await self.command_send_error(
                ctx, message="Action provided was either not unique or could not be found."
            )
            return

        try:
            new_status: AssignedCommitteeAction.Status = AssignedCommitteeAction.Status(status)
        except (ValueError, KeyError) as invalid_status:
            await self.command_send_error(
                ctx, message=f"Status ({status}) provided was not valid or could not be found."
            )
            logger.debug(invalid_status)
            return

        if not new_status:
            await self.command_send_error(
                ctx=ctx,
                message=f"Status ({status}) provided was not valid or could not be found.",
            )
            logger.debug("An invalid status was provided but did not raise an exception.")
            return

        await action.aupdate(status=new_status)

        await self._update_action_board()

        await ctx.respond(
            content=f"Status for action`{action.description}` updated to `{action.status}`",
            ephemeral=True,
        )

    @committee_actions.command(
        name="update-description", description="Update the description of the provided action."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to mark as completed.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_user_action_ids),  # type: ignore[arg-type]
        required=True,
        parameter_name="action_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="description",
        description="The description to be used for the action",
        input_type=str,
        required=True,
        parameter_name="action_description",
    )
    async def update_description(
        self, ctx: "TeXBotApplicationContext", action_id: str, new_description: str
    ) -> None:
        """
        Definition and callback response of the "update-description" command.

        Takes in an action id and description, retrieves the action from the ID
        and updates the action to with the new description.
        """
        if len(new_description) >= 200:
            await ctx.respond(
                content=":warning: The provided description was too long! No action taken."
            )
            return

        try:
            action_id_int: int = int(action_id)
        except ValueError:
            await self.command_send_error(
                ctx=ctx,
                message="Action ID entered was not valid! Please use the autocomplete.",
                logging_message=f"{ctx.user} entered action ID: {action_id} which was invalid",
            )
            return

        try:
            action: AssignedCommitteeAction = (
                await AssignedCommitteeAction.objects.select_related().aget(id=action_id_int)
            )
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await self.command_send_error(
                ctx=ctx, message="Action provided was either not unique or could not be found."
            )
            return

        old_description: str = action.description

        await action.aupdate(description=new_description)

        await self._update_action_board()

        await ctx.respond(
            content=f"Action `{old_description}` updated to `{action.description}`!"
        )

    @committee_actions.command(
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
    async def action_random_user(
        self, ctx: "TeXBotApplicationContext", action_description: str
    ) -> None:
        """
        Definition and callback response of the "action-random-user" command.

        Creates an action object with the specified description
        but randomises the committee member.
        """
        committee_role: discord.Role = await self.bot.committee_role
        committee_members: list[discord.Member] = committee_role.members

        if not committee_members:
            await ctx.respond(
                content=(
                    "No committee members were found to randomly select from! Command aborted."
                )
            )
            return

        index: int = random.randint(0, len(committee_members) - 1)  # noqa: S311

        try:
            action_user: discord.Member = committee_members[index]
        except IndexError:
            logger.debug("Index: %s was out of range! Printing list...", index)
            logger.debug(committee_members)
            await self.command_send_error(
                ctx=ctx,
                message=(
                    f"Index {index} out of range for {len(committee_members)} "
                    "committee members... check the logs!"
                ),
            )
            return

        try:
            await self._create_action(
                ctx=ctx, action_user=action_user, description=action_description
            )
            await ctx.respond(
                content=f"Action `{action_description}` created for: {action_user.mention}"
            )
        except (
            InvalidActionTargetError,
            InvalidActionDescriptionError,
        ) as creation_failed_error:
            await ctx.respond(content=creation_failed_error.message)
            return

    @committee_actions.command(
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
    async def action_all_committee(
        self, ctx: "TeXBotApplicationContext", action_description: str
    ) -> None:
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
            try:
                _: AssignedCommitteeAction | None = await self._create_action(
                    ctx=ctx, action_user=committee_member, description=action_description
                )
                success_members.append(committee_member)
            except (
                InvalidActionDescriptionError,
                InvalidActionTargetError,
            ) as creation_failed_error:
                failed_members += creation_failed_error.message + "\n"

        response_message: str = ""

        if success_members:
            response_message += (
                f"Successfully created action `{action_description}` for users: \n"
            )

            response_message += "\n".join(
                f"{success_member.mention}" for success_member in success_members
            )

            if len(failed_members) > 1:
                response_message += (
                    "\n\nThe following errors were also raised: \n" + failed_members
                )
        else:
            response_message += "Could not create any actions! See errors below: \n"

            response_message += failed_members

        await ctx.respond(content=response_message)

    @committee_actions.command(
        name="list", description="Lists all actions for a specified user"
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to list actions for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_committee_members),  # type: ignore[arg-type]
        required=False,
        default=None,
        parameter_name="action_member_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="ping",
        description="Triggers whether the message pings users or not.",
        input_type=bool,
        default=False,
        required=False,
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="status",
        description="The desired status of the action.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_action_status),  # type: ignore[arg-type]
        required=False,
        default=None,
        parameter_name="status",
    )
    async def list_user_actions(  # NOTE: Committee role check is not present because non-committee can have actions, and need to be able to list their own actions.
        self,
        ctx: "TeXBotApplicationContext",
        action_member_id: None | str,
        ping: bool,  # noqa: FBT001
        status: None | str,
    ) -> None:
        """
        Definition and callback of the "/list" command.

        Takes in a user and lists out their current actions.
        If no user is specified, the user issuing the command will be used.
        If a user has the committee role, they can list actions for other users.
        If a user does not have the committee role, they can only list their own actions.
        """
        if action_member_id is not None:
            action_member_id = action_member_id.strip()

        action_member: discord.Member | discord.User = (
            await self.bot.get_member_from_str_id(action_member_id)
            if action_member_id
            else ctx.user
        )

        if action_member != ctx.user and not await self.bot.check_user_has_committee_role(
            ctx.user
        ):
            await ctx.respond(
                content="Committee role is required to list actions for other users.",
                ephemeral=True,
            )
            logger.debug(
                (
                    "User: %s, tried to list actions for user: %s, "
                    "but did not have the committee role."
                ),
                ctx.user,
                action_member,
            )
            return

        if not status:
            user_actions = [
                action
                async for action in AssignedCommitteeAction.objects.filter(
                    (
                        Q(status=AssignedCommitteeAction.Status.IN_PROGRESS.value)
                        | Q(status=AssignedCommitteeAction.Status.BLOCKED.value)
                        | Q(status=AssignedCommitteeAction.Status.NOT_STARTED.value)
                    ),
                    discord_member__discord_id=action_member.id,
                )
            ]
        else:
            user_actions = [
                action
                async for action in AssignedCommitteeAction.objects.filter(
                    status=status,
                    discord_member__discord_id=action_member.id,
                )
            ]

        if not user_actions:
            await ctx.respond(
                content=(
                    (
                        f"User: {action_member.mention if ping else action_member} has no "
                        "in progress actions."
                    )
                    if not status
                    else "actions matching given filter."
                )
            )
            return

        actions_message: str = (
            f"Found {len(user_actions)} actions for user "
            f"{action_member.mention if ping else action_member}:"
            f"\n{
                '\n'.join(
                    str(action.description)
                    + f' ({action.status})'
                    for action in user_actions
                )
            }"
        )

        await ctx.respond(content=actions_message)

    @committee_actions.command(
        name="reassign", description="Reassign the specified action to another user."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to reassign.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_user_action_ids),  # type: ignore[arg-type]
        required=True,
        parameter_name="action_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to list actions for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_committee_members),  # type: ignore[arg-type]
        required=True,
        parameter_name="member_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def reassign_action(
        self, ctx: "TeXBotApplicationContext", action_id: str, member_id: str
    ) -> None:
        """Reassign the specified action to the specified user."""
        try:
            action_id_int: int = int(action_id)
        except ValueError:
            await self.command_send_error(
                ctx=ctx,
                message="Action ID entered was not valid! Please use the autocomplete.",
                logging_message=f"{ctx.user} entered action ID: {action_id} which was invalid",
            )
            return

        new_user_to_action: discord.Member = await self.bot.get_member_from_str_id(
            member_id,
        )

        try:
            action_to_reassign: AssignedCommitteeAction = (
                await AssignedCommitteeAction.objects.select_related().aget(id=action_id_int)
            )
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            await self.command_send_error(
                ctx, message="Action provided was either not unique or could not be found."
            )
            return

        if str(action_to_reassign.discord_member) == str(new_user_to_action.id):
            await ctx.respond(
                content=(
                    f"HEY! Action `{action_to_reassign.description}` is already assigned "
                    f"to user: {new_user_to_action.mention}\nNo action has been taken."
                )
            )
            return

        try:
            new_action: AssignedCommitteeAction | None = await self._create_action(
                ctx=ctx,
                action_user=new_user_to_action,
                description=action_to_reassign.description,
            )
            if new_action:
                await action_to_reassign.adelete()
                await ctx.respond(
                    content=(
                        f"Action `{new_action.description}` successfully "
                        f"reassigned to {new_user_to_action.mention}!"
                    )
                )
        except (
            InvalidActionDescriptionError,
            InvalidActionTargetError,
        ) as invalid_description_error:
            await ctx.respond(content=invalid_description_error.message)
            return

    @committee_actions.command(name="list-all", description="List all current actions.")
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="status-filter",
        description="The filter to apply to the status of actions.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_action_status),  # type: ignore[arg-type]
        required=False,
        default=None,
        parameter_name="status",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def list_all_actions(
        self,
        ctx: "TeXBotApplicationContext",
        status: str | None,
    ) -> None:
        """List all actions."""
        all_actions: dict[str, list[AssignedCommitteeAction]] = await self._get_all_actions()
        filtered_actions: dict[str, list[AssignedCommitteeAction]] = {
            discord_id: actions
            for discord_id, actions in all_actions.items()
            if not status or any(action.status == status for action in actions)
        }

        if not filtered_actions:
            await ctx.respond(content="No one has any actions that match the request!")
            logger.debug("No actions found with the status filter: %s", status)
            return

        all_actions_message: str = "\n".join(
            f"\n<@{discord_id}>, Actions:\n"
            f"{
                ', \n'.join(
                    action.status.emoji
                    + str(action.description)
                    + f' ({action.status})'
                    for action in actions
                    if action.discord_member.discord_id == discord_id
                )
            }"
            for discord_id, actions in filtered_actions.items()
        )

        await ctx.respond(content=all_actions_message)

    @committee_actions.command(
        name="delete", description="Deletes the specified action from the database completely."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="action",
        description="The action to delete.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_user_action_ids),  # type: ignore[arg-type]
        required=True,
        parameter_name="action_id",
    )
    async def delete_action(self, ctx: "TeXBotApplicationContext", action_id: str) -> None:
        """
        Definition & callback response of the "delete" command.

        Takes in an action as an argument and deletes it from the database.
        This command should be used for administrative purposes only, in most circumstances
        the update-status command should be used.
        """
        try:
            action_id_int: int = int(action_id)
        except ValueError:
            await self.command_send_error(
                ctx=ctx,
                message="Action ID entered was not valid! Please use the autocomplete.",
                logging_message=f"{ctx.user} entered action ID: {action_id} which was invalid",
            )
            return

        try:
            action: AssignedCommitteeAction = (
                await AssignedCommitteeAction.objects.select_related().aget(id=action_id_int)
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            await self.command_send_error(
                ctx=ctx, message="Action provided was either not unique or could not be found."
            )
            return

        action_description: str = action.description

        await action.adelete()

        await self._update_action_board()

        await ctx.respond(content=f"Action `{action_description}` successfully deleted.")


class CommitteeActionsTrackingContextCommandsCog(CommitteeActionsTrackingBaseCog):
    """Cog class to define the actions tracking message context commands."""

    @discord.message_command(  # type: ignore[no-untyped-call, misc]
        name="Action Message Author",
        description="Creates a new action for the message author using the message content.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def action_message_author(  # type: ignore[misc]
        self, ctx: "TeXBotApplicationContext", message: discord.Message
    ) -> None:
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

        try:
            await self._create_action(
                ctx=ctx, action_user=actioned_message_user, description=actioned_message_text
            )
            await ctx.respond(
                content=(
                    f"Action `{actioned_message_text}` created "
                    f"for: {actioned_message_user.mention}"
                )
            )
        except (
            InvalidActionTargetError,
            InvalidActionDescriptionError,
        ) as creation_failure_error:
            await ctx.respond(content=creation_failure_error.message)
