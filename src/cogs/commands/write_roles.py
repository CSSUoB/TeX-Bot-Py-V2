import logging

from discord import ApplicationContext, Bot, ChannelType, Guild, Member, Role, TextChannel, utils
from discord.ext import commands

from utils import settings


class Write_Roles(commands.Cog):
    ROLES_MESSAGES: tuple[str, str, str, str] = (
        "\nReact to this message to get pronoun roles\n🇭 - He/Him\n🇸 - She/Her\n🇹 - They/Them",
        "_ _\nReact to this message to get year group roles\n0️⃣ - Foundation Year\n1️⃣ - First Year\n2️⃣ - Second Year\n🇫 - Final Year (incl. 3rd Year MSci/MEng)\n🇮 - Year in Industry\n🇦 - Year Abroad\n🇹 - Post-Graduate Taught (Masters/MSc) \n🇷 - Post-Graduate Research (PhD) \n🅰️ - Alumnus\n🇩 - Postdoc",
        "_ _\nReact to this message to join the **opt in channels**\n💬 - Serious Talk\n🏡 - Housing\n🎮 - Gaming\n📺 - Anime\n⚽ - Sport\n💼 - Industry\n⛏️ - Minecraft\n🌐 - CSS Website\n🔖 - Archivist",
        "_ _\nReact to this message to opt in to News notifications\n🔈- Get notifications when we `@News`\n🔇- Don't get notifications when we `@News`\n_ _\n> We will still use `@everyone` messages if there is something urgent",
    )

    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    # noinspection SpellCheckingInspection
    @commands.slash_command(
        name="writeroles",
        description="Populates #roles with the correct messages."
    )
    async def write_roles(self, ctx: ApplicationContext):
        guild: Guild | None = self.bot.get_guild(settings["DISCORD_GUILD_ID"])
        if guild is None:
            await ctx.respond(f"""⚠️There was an error when trying to send messages:⚠️️\n`Server with id \"{settings["DISCORD_GUILD_ID"]}\" does not exist.`""", ephemeral=True)
            return

        roles_channel: TextChannel | None = utils.get(guild.text_channels, name="roles")
        if roles_channel is None:
            await ctx.respond("⚠️There was an error when trying to send messages:⚠️️\n`Text channel with name \"roles\" does not exist.`", ephemeral=True)
            return

        guild_member: Member | None = await guild.fetch_member(ctx.user.id)
        if guild_member is None:
            await ctx.respond("⚠️There was an error when trying to send messages:⚠️️\n`You must be a member of the CSS Discord server to run this command.`", ephemeral=True)
            return

        committee_role: Role | None = utils.get(guild.roles, name="Committee")
        if committee_role is None:
            await ctx.respond("⚠️There was an error when trying to send messages:⚠️️\n`Role with name \"Committee\" does not exist.`", ephemeral=True)
            return

        if committee_role not in guild_member.roles:
            await ctx.respond("⚠️There was an error when trying to send messages:⚠️️\n`You must have the \"Committee\" role to run this command.`", ephemeral=True)
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

    @commands.slash_command(
        name="newping",
        description="test"
    )
    async def newping(self, ctx: ApplicationContext):
        await ctx.respond("a tessssst")


def setup(bot: Bot):
    bot.add_cog(Write_Roles(bot))
