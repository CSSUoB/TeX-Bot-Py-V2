import logging
import random

import discord
from discord import ApplicationContext, Bot, Guild, Member, Role, TextChannel
from discord.ext import commands

from setup import settings


class Commands(commands.Cog):
    ROLES_MESSAGES: tuple[str, str, str, str] = (
        "\nReact to this message to get pronoun roles\n🇭 - He/Him\n🇸 - She/Her\n🇹 - They/Them",
        "_ _\nReact to this message to get year group roles\n0️⃣ - Foundation Year\n1️⃣ - First Year\n2️⃣ - Second Year\n🇫 - Final Year (incl. 3rd Year MSci/MEng)\n🇮 - Year in Industry\n🇦 - Year Abroad\n🇹 - Post-Graduate Taught (Masters/MSc) \n🇷 - Post-Graduate Research (PhD) \n🅰️ - Alumnus\n🇩 - Postdoc",
        "_ _\nReact to this message to join the **opt in channels**\n💬 - Serious Talk\n🏡 - Housing\n🎮 - Gaming\n📺 - Anime\n⚽ - Sport\n💼 - Industry\n⛏️ - Minecraft\n🌐 - CSS Website\n🔖 - Archivist",
        "_ _\nReact to this message to opt in to News notifications\n🔈- Get notifications when we `@News`\n🔇- Don't get notifications when we `@News`\n_ _\n> We will still use `@everyone` messages if there is something urgent",
    )

    def __init__(self, bot: TeXBot):
        self.bot: TeXBot = bot

    @discord.slash_command(description="Replies with Pong!")
    async def ping(self, ctx: ApplicationContext):
        ctx.defer()

        logging.warning(f"{ctx.interaction.user} made me pong!!")

        try:
            pong_text: str = random.choices(
                [
                    "Pong!",
                    "64 bytes from TeX: icmp_seq=1 ttl=63 time=0.01 ms"
                ], weights=settings["PING_COMMAND_EASTER_EGG_WEIGHTS"]
            )[0]
        except Exception:
            await ctx.respond("⚠️There was an error when trying to reply with Pong!!.⚠️", ephemeral=True)
            raise
        else:
            await ctx.respond(pong_text)

    @discord.slash_command(description="Displays information about the source code of this bot.")
    async def source(self, ctx: ApplicationContext):
        await ctx.respond(
            "TeX is an open-source project made specifically for the CSS Discord! You can see and contribute to the source code at https://github.com/CSSUoB/TeX-Bot-Py"
        )

    # noinspection SpellCheckingInspection
    @discord.slash_command(
        name="writeroles",
        description="Populates #roles with the correct messages."
    )
    async def write_roles(self, ctx: ApplicationContext):
        ctx.defer()

        guild: Guild | None = self.bot.get_guild(settings["DISCORD_GUILD_ID"])
        if guild is None:
            await ctx.respond(
                f"""⚠️There was an error when trying to send messages:⚠️️\n`Server with id \"{settings["DISCORD_GUILD_ID"]}\" does not exist.`""",
                ephemeral=True
            )
            return

        roles_channel: TextChannel | None = discord.utils.get(guild.text_channels, name="roles")
        if roles_channel is None:
            await ctx.respond(
                "⚠️There was an error when trying to send messages:⚠️️\n`Text channel with name \"roles\" does not exist.`",
                ephemeral=True
            )
            return

        guild_member: Member | None = await guild.fetch_member(ctx.user.id)
        if guild_member is None:
            await ctx.respond(
                "⚠️There was an error when trying to send messages:⚠️️\n`You must be a member of the CSS Discord server to run this command.`",
                ephemeral=True
            )
            return

        committee_role: Role | None = discord.utils.get(guild.roles, name="Committee")
        if committee_role is None:
            await ctx.respond(
                "⚠️There was an error when trying to send messages:⚠️️\n`Role with name \"Committee\" does not exist.`",
                ephemeral=True
            )
            return

        if committee_role not in guild_member.roles:
            await ctx.respond(
                "⚠️There was an error when trying to send messages:⚠️️\n`You must have the \"Committee\" role to run this command.`",
                ephemeral=True
            )
            return

        try:
            roles_message: str
            for roles_message in self.ROLES_MESSAGES:
                await roles_channel.send(roles_message)
        except Exception:
            await ctx.respond("⚠️There was an error when trying to send messages.⚠️", ephemeral=True)
            raise
        else:
            await ctx.respond("All messages sent successfully.", ephemeral=True)


def setup(bot: TeXBot):
    bot.add_cog(Commands(bot))
