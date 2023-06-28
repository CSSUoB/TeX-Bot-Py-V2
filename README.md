# TeX-Bot-Py

TeX-Bot, but back in Python! This is a [Discord bot](https://discord.com/build/app-developers) used for managing the [CSS Discord server](https://cssbham.com/discord).

## Error Codes

Users of the bot may encounter error codes when attempting to execute slash-commands, the list of error code descriptions is given here:

* `E1011` - The value for the environment variable `DISCORD_GUILD_ID` is an ID that references a Discord server that does not exist
* `E1021` - The CSS Discord server does not contain a role with the name "Committee" (required for the `/writeroles`, `/editmessage` & `/induct` commands)
* `E1022` - The CSS Discord server does not contain a role with the name "Guest" (required for the `/induct` & `/makemember` commands and the `kick_no_introduction_members` & `introduction_reminder` tasks)
* `E1023` - The CSS Discord server does not contain a role with the name "Member" (required for the `/makemember` command)
* `E1024` - The CSS Discord server does not contain a role with the name "Archivist" (required for the `/archive` command)
* `E1031` - The CSS Discord server does not contain a text channel with the name "#roles" (required for the `/writeroles` command)
* `E1032` - The CSS Discord server does not contain a text channel with the name "#general" (required for the `/induct` command)
* `E1041` - The guild member IDs could not be retrieved from the MEMBERS_PAGE_URL

## Dependencies

Ensure that you have [Poetry](https://python-poetry.org/) & [mypy](https://www.mypy-lang.org/) installed, then navigate to the root folder and run the following command:

```shell
poetry install
```

## Setup

You'll need to create a Discord bot of your own in the [Discord Developer Portal](https://discord.com/developers/applications). It's also handy if you have an empty server (or "guild") for you to test in.

You can retrieve the correct invite URL to use by navigating to the root folder, then running the following commands:

```shell
poetry shell
```
```shell
python utils.py generate_invite_url --discord_bot_application_id="[Replace with your Discord application ID]" --discord_guild_id="[Replace with the ID of the CSS Discord server]"
```

You'll also need to set a number of environment variables:

* `DISCORD_BOT_TOKEN`: The Discord token for the bot you created (available on your bot page in the [Developer Portal](https://discord.com/developers/applications)).
* `DISCORD_GUILD_ID`: The ID of the CSS Discord server.
* `DISCORD_LOG_CHANNEL_ID`: The ID of the text channel in the CSS Discord server where error logs should be sent. (This is optional and if it is not provided, error logs will be sent to the console only)
* `MEMBERS_PAGE_URL`: The URL of the CSS members page (currently found on the Guild of Students website, make sure it's sorted by group).
* `MEMBERS_PAGE_COOKIE`: The CSS members page session cookie (probably listed as `.ASPXAUTH`, gives the bot permission to view your members page as if it were logged in to the website as a Committee member, you can extract this from your web browser after logging into the CSS members page).

You can put these in a `.env` file in the root folder as it uses [python-dotenv](https://saurabh-kumar.com/python-dotenv/), so you don't have to keep them in your environment. There is an `example.env` file in the repo that you can rename and populate.

There are also many other configurations that can be changed, in order to alter the behaviour of the bot. These are all listed in the `example.env` file, along with the behaviours that will change.

## Contributions

Contributions are welcome. If you want to contribute, please raise a PR, and we'll review, test and (likely) merge it. Please comment on issues you'd like to work on for assignment to prevent duplication of work. If you find any bugs/problems or have any feature suggestion, please raise an issue.

Please utilise the [Pycharm `codeStyleConfig.xml`](https://www.jetbrains.com/help/pycharm/configuring-code-style.html) file and [mypy](https://www.mypy-lang.org/) type checking so that the repo has a consistent style.
