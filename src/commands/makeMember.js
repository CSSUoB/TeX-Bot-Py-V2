const { SlashCommandBuilder } = require("@discordjs/builders");
const axios = require("axios");
const cheerio = require("cheerio");
const tough = require("tough-cookie");
require("../../config/config.js");

const cookie = new tough.Cookie({
  key: ".ASPXAUTH",
  value: process.env.UNION_COOKIE,
  domain: "www.guildofstudents.com",
});

const wait = require("util").promisify(setTimeout);

module.exports = {
  data: new SlashCommandBuilder()
    .setName("makemember")
    .setDescription(
      "Gives you the Member role when supplied with an appropriate Student ID."
    )
    .addStringOption((option) =>
      option
        .setName("studentid")
        .setDescription("Your UoB Student ID")
        .setRequired(true)
    ),
  async execute(interaction) {
    await interaction.deferReply({ ephemeral: true });
    await wait(1000);

    const memberArray = this.getMembers();

    if (
      (await memberArray).includes(interaction.options.getString("studentid"))
    ) {
      const role = interaction.guild.roles.cache.find(
        (r) => r.name === "Member"
      );
      await interaction.member.roles.add(role).catch(console.error);

      await interaction.editReply({
        content: "Made you a Member!",
        ephemeral: true,
      });
    } else {
      await interaction.editReply({
        content:
          "Invalid Student ID supplied. Please contact a Committee member.",
        ephemeral: true,
      });
    }
  },
  async getMembers() {
    const result = await axios({
      method: "get",
      url: process.env.UNION_URL,
      headers: {
        Cookie: cookie,
      },
      withCredentials: true,
    });

    if (!result) {
      console.log("req err");
      return;
    }

    const memberArray = [];

    const $ = cheerio.load(result.data);
    $(
      "#ctl00_Main_rptGroups_ctl05_gvMemberships > tbody > tr > td:nth-child(2)"
    ).each((index, element) => {
      memberArray[index] = $(element).text();
    });

    return memberArray;
  },
};
