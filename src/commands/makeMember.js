const { SlashCommandBuilder } = require("@discordjs/builders");
const axios = require("axios");
const cheerio = require("cheerio");
const tough = require("tough-cookie");
const fs = require("fs");
const crypto = require("crypto");
require("../../config/config.js");

const cookie = new tough.Cookie({
  key: ".ASPXAUTH",
  value: process.env.UNION_COOKIE,
  domain: "www.guildofstudents.com",
});

const hash = crypto.createHash("sha256");

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
  usedIDs: [],
  async execute(interaction) {
    await interaction.deferReply({ ephemeral: true });
    await wait(1000);

    const memberArray = this.getMembers();

    if (
      this.usedIDs.includes(
        hash.update(interaction.options.getString("studentid")).digest("hex")
      )
    ) {
      return await interaction.editReply({
        content:
          "This id has already been used. Please contact a Committee member if this is an error.",
      });
    } else if (
      interaction.member.roles.cache.find((r) => r.name === "Member")
    ) {
      return await interaction.editReply({
        content: "You're already a member - why are you trying this again?",
      });
    }

    if (
      (await memberArray).includes(interaction.options.getString("studentid"))
    ) {
      this.usedIDs.push(
        hash.update(interaction.options.getString("studentid")).digest("hex")
      );
      console.log(this.usedIDs);

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
  updateJSON(id) {
    let obj = {
      ids: this.usedIDs,
    };
    let json = JSON.stringify(obj);
    fs.writeFile(
      "member.json",
      json,
      "utf8",
      function readFileCallback(err, data) {
        if (err) {
          console.error(err);
        } else {
          obj = JSON.parse(data);
          obj.ids.push(id);
          json = JSON.stringify(obj);
          fs.writeFile("member.json", json, "utf8", callback);
        }
      }
    );
  },
};
