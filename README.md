# TeX-Bot-Py

TeX-Bot, but back in Python! This is a [Discord bot](https://discord.com/build/app-developers) used for managing the [CSS Discord server](https://cssbham.com/discord).

## Error Codes

Users of the bot may encounter error codes when attempting to execute slash-commands, the list of error code descriptions is given here:

* `E1011` - The value for the environment variable `DISCORD_GUILD_ID` is an ID that references a Discord server that does not exist
* `E1021` - The CSS Discord server does not contain a role with the name "Committee" (required for the `/writeroles`, `/editmessage` & `/induct` commands)
* `E1022` - The CSS Discord server does not contain a role with the name "Guest" (required for the `/induct` command)
* `E1023` - The CSS Discord server does not contain a role with the name "Member" (required for the `/makemember` command)
* `E1031` - The CSS Discord server does not contain a text channel with the name "#roles" (required for the `/writeroles` command)
* `E1032` - The CSS Discord server does not contain a text channel with the name "#general" (required for the `/induct` command)
* `E1041` - The guild member IDs could not be retrieved from the MEMBERS_PAGE_URL
* `E1051` - The messages JSON file could not be correctly decoded (required for the `/writeroles` & `/induct` commands)
* `E1052` - The messages JSON file does not contain a list of roles messages at the key `"roles_messages"` (required for the `/writeroles` command)
* `E1053` - The messages JSON file does not contain a list of welcome messages at the key `"welcome_messages"` (required for the `/induct` command)

## Dependencies

Ensure that you have [Poetry](https://www.mypy-lang.org/) & [mypy](https://www.mypy-lang.org/) installed, then navigate to the root folder and run the following command:

```shell
poetry install
```

## Setup

You'll need to create a Discord bot of your own in the [Discord Developer Portal](https://discord.com/developers/applications). It's also handy if you have an empty server (or "guild") for you to test in.

You can retrieve the correct invite URL to use by navigating to the root folder, then running the following command:

```shell
python -c "from . import utils; print(utils.get_oauth_url())"
```

You'll also need to set a number of environment variables:

* `DISCORD_BOT_TOKEN`: The Discord token for the bot you created (available on your bot page in the [Developer Portal](https://discord.com/developers/applications)).
* `DISCORD_BOT_APPLICATION_ID`: The Discord application ID of the bot (also available on the main page of your application in the [Developer Portal](https://discord.com/developers/applications)).
* `DISCORD_GUILD_ID`: The ID of the CSS Discord server.
* `MEMBERS_PAGE_URL`: The URL of the CSS members page (currently found on the Guild of Students website, make sure it's sorted by group).
* `MEMBERS_PAGE_COOKIE`: The CSS members page session cookie (probably listed as `.ASPXAUTH`, gives the bot permission to view your members page as if it were logged in to the website as a Committee member, you can extract this from your web browser after logging into the CSS members page).

You can put these in a `.env` file in the root folder as it uses [python-dotenv](https://saurabh-kumar.com/python-dotenv/), so you don't have to keep them in your environment. There is an `example.env` file in the repo that you can rename and populate.

## Contributions

Contributions are welcome. If you want to contribute, please raise a PR, and we'll review, test and (likely) merge it. Please comment on issues you'd like to work on for assignment to prevent duplication of work. If you find any bugs/problems or have any feature suggestion, please raise an issue.

Please utilise the [Pycharm `codeStyleConfig.xml`](https://www.jetbrains.com/help/pycharm/configuring-code-style.html) file and [mypy](https://www.mypy-lang.org/) type checking so that the repo has a consistent style.
