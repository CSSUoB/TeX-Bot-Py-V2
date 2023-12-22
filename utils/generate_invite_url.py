"""Utility function to generate the URL to invite the bot to a given Discord guild."""


from collections.abc import Sequence

__all__: Sequence[str] = ["InviteURLGenerator"]

import os
import re
import sys
from argparse import Namespace
from typing import Final

import discord

from utils.base_utility_function import UtilityFunction


class InviteURLGenerator(UtilityFunction):
    """Utility function to generate the URL to invite the bot to a given Discord guild."""

    NAME: str = "generate_invite_url"
    DESCRIPTION: str = "Generate the URL to invite the bot to a given Discord guild"

    @classmethod
    def attach_to_parser(cls, parser: UtilityFunction.SubParserAction) -> None:
        """
        Add a subparser to the provided argument parser.

        This allows the subparser to retrieve arguments specific to this utility function.
        """
        super().attach_to_parser(parser)
        if parser not in cls._function_subparsers:
            FUNCTION_SUBPARSER_DOES_NOT_EXIST_MESSAGE: Final[str] = (
                f"""{"self.function_subparser"!r} does not exist."""
            )
            raise RuntimeError(FUNCTION_SUBPARSER_DOES_NOT_EXIST_MESSAGE)

        cls._function_subparsers[parser].add_argument(
            "discord_bot_application_id",
            help="Must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)"
        )
        cls._function_subparsers[parser].add_argument(
            "discord_guild_id",
            nargs="?",
            help=(
                "The value of the environment variable DISCORD_GUILD_ID is used "
                "if this argument is omitted. Must be a valid Discord guild ID "
                "(see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
            )
        )

    @classmethod
    def run(cls, parsed_args: Namespace, parser: UtilityFunction.SubParserAction) -> int:
        """Execute the logic that this util function provides."""
        if parser not in cls._function_subparsers:
            FUNCTION_SUBPARSER_DOES_NOT_EXIST_MESSAGE: Final[str] = (
                f"""{"self.function_subparser"!r} does not exist."""
            )
            raise RuntimeError(FUNCTION_SUBPARSER_DOES_NOT_EXIST_MESSAGE)

        if not re.match(r"\A\d{17,20}\Z", parsed_args.discord_bot_application_id):
            cls._function_subparsers[parser].error(
                "discord_bot_application_id must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)"
            )

        discord_guild_id: str = parsed_args.discord_guild_id or ""
        if not discord_guild_id:
            import dotenv

            dotenv.load_dotenv()
            discord_guild_id = os.getenv("DISCORD_GUILD_ID", "")

            if not discord_guild_id:
                cls._function_subparsers[parser].error(
                    "discord_guild_id must be provided as an argument "
                    "to the generate_invite_url utility function "
                    "or otherwise set the DISCORD_GUILD_ID environment variable"
                )

        if not re.match(r"\A\d{17,20}\Z", discord_guild_id):
            cls._function_subparsers[parser].error(
                "discord_guild_id must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
            )

        sys.stdout.write(f"""{cls.generate_invite_url(
            parsed_args.discord_bot_application_id,
            int(discord_guild_id)
        )}\n""")
        return 0

    # noinspection PyShadowingNames
    @staticmethod
    def generate_invite_url(discord_bot_application_id: str, discord_guild_id: int) -> str:
        """
        Generate the correct OAuth invite URL for the bot.

        This invite URL directs to the given Discord guild and requests only the permissions
        required for the bot to run.
        """
        return discord.utils.oauth_url(
            client_id=discord_bot_application_id,
            permissions=discord.Permissions(
                manage_roles=True,
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True,
                read_message_history=True,
                mention_everyone=True,
                add_reactions=True,
                use_slash_commands=True,
                kick_members=True,
                manage_channels=True,
                view_audit_log=True
            ),
            guild=discord.Object(id=discord_guild_id),
            scopes=("bot", "applications.commands"),
            disable_guild_select=True
        )
