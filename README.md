# TeX-Bot-JS

TeX-Bot, but now in JS! This is a Discord bot used for managing the CSS Discord server.

## Dependencies

Ensure you have NodeJS and Yarn installed, then navigate to the root folder and enter the following into the console:

> yarn

## Setup

You'll need to create a Discord bot of your own in the [Discord Developer Portal](https://discord.com/developers/applications). It's also handy if you have an empty server (or "guild") for you to test in.

You'll need to set a number of environment variables:

-   DISCORD_TOKEN -> The Discord token for the bot you created (available on your bot page in the Developer Portal).

You can put these in a `.env` file in the root folder as it uses dotenv so you don't have to keep them in your environment. There is an `example.env` file in the repo that you can rename and populate.

## Contributions

Contributions are welcome. If you want to contribute, please raise a PR and we'll review, test and (likely) merge it. Please comment on issues you'd like to work on for assignment to prevent duplicatation of work. If you find any bugs/problems or have any feature suggestion, please raise an issue.

Please utiise the Prettier and ESLint files so that the repo has a consistent style.
