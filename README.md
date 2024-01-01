# TeX-Bot-Py

[TeX-Bot](https://github.com/CSSUoB/TeX-Bot-JS), but back in Python!
This is a [Discord bot](https://discord.com/build/app-developers)
used for managing a community group's Discord guild.

Featured in the [CSS Discord guild](https://cssbham.com/discord).

[![Current Version](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FCSSUoB%2FTeX-Bot-Py-V2%2Fmain%2Fpyproject.toml&query=%24.tool.poetry.version&label=TeX-Bot)](https://github.com/CSSUoB/TeX-Bot-Py-V2/tree/main)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/release/python-3116/)
[![py-cord Version](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FCSSUoB%2FTeX-Bot-Py-V2%2Fmain%2Fpyproject.toml&query=%24.tool.poetry.dependencies%5B'py-cord-dev'%5D&label=py-cord)](https://pycord.dev/)
[![Tests](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/tests.yaml/badge.svg)](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/tests.yaml)
[![mypy passing](https://img.shields.io/badge/mypy-checked-%232EBB4E&label=mypy)](https://www.mypy-lang.org/)
[![pymarkdown passing](https://img.shields.io/badge/pymarkdown-passing-%232EBB4E&label=pymarkdown)](https://github.com/jackdewinter/pymarkdown)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://ruff.rs/)

## Terminology

### "Guild" & "Server"

Confusingly, Discord uses the term "guild" to refer to a Discord "server", when communicating
with developers.
Therefore, the same terminology ("guild") will be used across all documentation
in this project.

The term "main guild" is used throughout the code in this repository
to refer specifically to your community group's main Discord guild.

### "User", "Member" & "Guest"

There may be confusion between the terms "user" and "member".

In the context of Discord itself, a "user" object represents a Discord account
not connected to any specific guild.
Therefore, it can be messaged via DM or be retrieved via its snowflake ID,
but not much else can be done with it.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/user)
& [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#users)
for more information.)

In contrast, a Discord "member" object is a "user" attached to a specific guild.
Therefore, it can have roles, be banned & have many other actions applied to it.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/guild#guild-member-object)
& [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#discord.Member)
for more information.)

In the context of your community group's membership structure, a "member" is a person
that has purchased a membership to join your community group.
This is in contrast to a "guest", which is a person that has not purchased a membership.
Guests often can only attend events that are open to anyone (i.e. **not** members only),
and have limited communication/perks within your Discord guild.
Some commands may require you to create roles within your Discord guild,
to differentiate between these different types of people.

In some other contexts, the term "user" may be used to refer to any person/organisation
making use of this project.
(E.g. the description within [the **Error Codes** section](#error-codes).)

## Error Codes

Users of the bot may encounter error codes when attempting to execute slash-commands,
the list of error code descriptions is given here:

* `E1011` - The value for the environment variable `DISCORD_GUILD_ID` is an ID
that references a Discord guild that does not exist
* `E1021` - Your Discord guild does not contain a role with the name "@Committee"
(required for the `/writeroles`, `/editmessage`, `/induct`, `/strike`, `/archive`,
`/delete-all` & `/ensure-members-inducted` commands)
* `E1022` - Your Discord guild does not contain a role with the name "@Guest"
(required for the `/induct`, `/stats`, `/archive` & `/ensure-members-inducted` commands and
the `kick_no_introduction_discord_members` & `introduction_reminder` tasks)
* `E1023` - Your Discord guild does not contain a role with the name "@Member"
(required for the `/makemember` & `/ensure-members-inducted` command)
* `E1024` - Your Discord guild does not contain a role with the name "@Archivist"
(required for the `/archive` command)
* `E1031` - Your Discord guild does not contain a text channel with the name "#roles"
(required for the `/writeroles` command)
* `E1032` - Your Discord guild does not contain a text channel with the name "#general"
(required for the `/induct` command)
* `E1041` - The community group member IDs could not be retrieved from the `MEMBERS_LIST_URL`
(If your community group is a Guild of Students society,
the community group member IDs will be a list of UoB IDs)
* `E1042` - The reference to the `@everyone` role could not be correctly retrieved
* `E1043` - A button callback interaction did not contain the related user

## Logging Error Levels

When the bot logs an error, an associated log-level is used.
Below are the explanations of what effects/causes each log-level represents.

* `WARNING` - An error occurred that did **not result in any failure
to complete the current request/interaction**.
However, some minor data loss/inconsistencies may have occurred.
These may require a committee member to make some manual fixes or raise an issue about a bug.
* `ERROR` - The current **request/interaction could *not* be completed**, due to a major error.
The problem that caused the error should be addressed immediately,
or otherwise the bot should be manually shut down to prevent further errors.
* `CRITICAL` - An **unrecoverable error occurred**.
This level of error will cause the bot to shut down,
as the bot has identified that the problem can only be solved
by fixing one or more of the configuration environment variables.

## Repeated Tasks Conditions

The configuration variables `SEND_INTRODUCTION_REMINDERS`, `SEND_GET_ROLES_REMINDERS` &
`KICK_NO_INTRODUCTION_DISCORD_MEMBERS` determine whether their related tasks should run.
However, because these are rather annoying/drastic actions to be executed automatically,
there are additional conditions that must be met on a per-member basis
for the action to trigger.
The conditions for each task are listed below, along with the additional environment variables
that can be used to configure the conditions to suit your needs.

| Task Name                              | Enable/Disable                                                                                                                                                                                                                                       | Per-Member Conditions                                                                                                                                                                                                                                                                                                                                                                                                                      | Scheduled Interval                                                                                                                                                                                                                                                                                |
|----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `introduction_reminder`                | `SEND_INTRODUCTION_REMINDERS`:<br/>* `Once` - Only send the introduction reminder once (even if they later delete the message)<br/>* `Interval` - Send an introduction reminder at a set interval<br/>* `False` - Do not send introduction reminders | * The Discord member has not been inducted (does not have the Guest role)<br/>* The time since the Discord member joined is greater than the maximum out of 1 day or one third of `KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY`<br/>* The Discord member has not opted out of introduction reminders<br/>* The Discord member has not already been sent an introduction reminder (only applied when `SEND_INTRODUCTION_REMINDERS` == `Once` | The interval of time between this task running is determined by `SEND_INTRODUCTION_REMINDERS_INTERVAL`. (When `SEND_INTRODUCTION_REMINDERS` == `Once`, all Discord members will still be checked at this interval just not sent a message if they have already been sent an introduction reminder |
| `kick_no_introduction_discord_members` | `KICK_NO_INTRODUCTION_DISCORD_MEMBERS`:<br/>* `True` - Discord members that meet the per-member conditions will be kicked from your guild<br/>* `False` - No Discord members will ever be kicked                                                     | * The Discord member has not been inducted (does not have the Guest role)<br/>* The time since the Discord member joined is greater than `KICK_NO_INTRODUCTION_DISCORD_MEMBERS_DELAY`                                                                                                                                                                                                                                                      | This task is run every 24 hours                                                                                                                                                                                                                                                                   |
| `get_roles_reminder`                   | `SEND_GET_ROLES_REMINDERS`:<br/>* `True` - A single reminder for the Discord member to get roles will be sent to them only once (even if they later delete the message)<br/>* `False` - Do not send any reminders for Discord members to get roles   | * The Discord member has been inducted (has the Guest role)<br/>* The Discord member does not have any of the opt-in roles (E.g. First Year or Anime) (having the green Member role or even the Committee role makes no difference)<br/>* The time since the Discord member was inducted (gained the guest role) is greater than 1 day<br/>* The Discord member has not yet been sent a reminder to get roles                              | The interval of time between this task running is determined by `SEND_GET_ROLES_REMINDERS_INTERVAL`                                                                                                                                                                                               |

## Production Deployment

The only supported way to deploy TeXBot in production
is by using our pre-built [docker container](https://www.docker.com/resources/what-container/).
It is [built automatically](.github/workflows/update-container-image.yaml)
when new changes are made to [the 'main' branch](https://github.com/CSSUoB/TeX-Bot-JS/tree/main),
and can be pulled from the [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
with this identifier: `ghcr.io/CSSUoB/texbot-py-v2:latest`.
An introduction on how to use a docker-compose deployment can be found [here](https://docs.docker.com/get-started/08_using_compose/).

Before running the container, some [environment variables](https://en.wikipedia.org/wiki/Environment_variable)
will need to be set.
These can be defined in your `docker-config.yaml` file.
The required [environment variables](https://en.wikipedia.org/wiki/Environment_variable)
are explained within [the **Setting Environment Variables** section](#setting-environment-variables).

## Local Deployment

### Installing Dependencies

Ensure that you have [Poetry](https://python-poetry.org/) installed.
Then install all the required dependencies, by navigating to the repository's root folder
and running the following command:

```shell
poetry install --no-root --sync
```

The [`--no-root` flag](https://python-poetry.org/docs/cli/#options-2)
installs the dependencies without installing the root project as a package.
Poetry attempts to install the project as a package by default
because Poetry is often used to develop library packages,
which need to be installed themselves.

The [`--sync` flag](https://python-poetry.org/docs/cli/#options-2)
uninstalls any additional packages that have already been installed in the local environment,
but are not required in the [pyproject.toml](pyproject.toml)

### Activating The Poetry Environment

To use the installed dependencies,
the environment they were installed within must be activated.
The easiest way to do this (as described by [Poetry's guide](https://python-poetry.org/docs/basic-usage/#activating-the-virtual-environment))
is with the below command:

```shell
poetry shell
```

If you do not want to activate the virtual environment,
every command can be run prepended with `poetry run`,
to run the subsequent command within the Poetry context.
(Every command within the documentation within this project
will include the `poetry run` prefix for convenience.
**It can be excluded if you have already activated the virtual environment.**)

### Creating Your Bot

You'll need to create a Discord bot of your own in the [Discord Developer Portal](https://discord.com/developers/applications).
It's also handy if you have an empty guild for you to test in.

You can retrieve the correct invite URL to use by navigating to the root folder,
then running the following command:

```shell
poetry run python -m utils generate_invite_url {discord_bot_application_id} {discord_guild_id}
```

### Setting Environment Variables

You'll also need to set a number of [environment variables](https://en.wikipedia.org/wiki/Environment_variable)
before running the bot:

* `DISCORD_BOT_TOKEN`: The Discord token for the bot you created.
(The token is available on your bot page in the [Developer Portal](https://discord.com/developers/applications).)
* `DISCORD_GUILD_ID`: The ID of your Discord guild.
* `DISCORD_LOG_CHANNEL_WEBHOOK_URL`: The [webhook URL](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
of the Discord text channel where error logs should be sent.
(This is optional. Error logs will always be sent to the console,
this setting allows them to also be sent to a Discord log channel.)
* `MEMBERS_LIST_URL`: The URL to retrieve the list of IDs of people
that have purchased a membership to your community group.
(The CSS' members-list is currently found on the Guild of Students website.
If your members-list is also found on the Guild of Students website,
ensure the URL includes the "sort by groups" option,
so that all members are visible without pagination.)
* `MEMBERS_LIST_URL_SESSION_COOKIE`: The members-list URL session cookie.
(If your group's members-list is stored at a URL that requires authentication,
this session cookie should authenticate the bot to view your group's members-list,
as if it were logged in to the website as a Committee member.
This can be extracted from your web-browser,
after logging in to view your members-list yourself.
It will probably be listed as a cookie named `.ASPXAUTH`.)

You can put these in a `.env` file in the root folder,
as [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
is used to collect all [environment variables](https://en.wikipedia.org/wiki/Environment_variable).
There is an `example.env` file in the repo that you can rename and populate.

There are also many other configurations that can be changed
in order to alter the behaviour of the bot.
These are all listed in the `example.env` file, along with the behaviours that will change.

Any variables, in the `example.env` file,
marked with `# !!REQUIRED!!` must be set before running the bot.
All other variables are optional and their default values are shown as the example value
for each variable in the `example.env` file.

### Running The Bot

Once everything is set up, you should be able to execute the following command
to automatically run the bot & connect it to your Discord guild:

```shell
poetry run python -m main
```

## Contributing

Contributions are welcome.
If you want to contribute, please [create](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request)
a [PR](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests),
and we'll review, test and (likely) merge it.
Please comment on any [issues](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues)
you'd like to work on, to prevent duplication of work.
If you find any bugs/problems or have any feature suggestions, please [create](https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-an-issue)
an [issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues).

Before making contributions, it is highly suggested to read [CONTRIBUTING.md](CONTRIBUTING.md).
This will ensure your code meets the standard required for this project
and gives you the greatest chances of your contributions being merged.
