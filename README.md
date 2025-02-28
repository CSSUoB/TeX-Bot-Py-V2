# TeX-Bot-Py-V2

[![Python Version](https://img.shields.io/badge/Python-3.12-blue?&logo=Python&logoColor=white)](https://python.org/downloads/release/python-3122)
[![Pycord Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Ftoml-version-finder.carrotmanmatt.com%2Flock%2FCSSUoB%2FTeX-Bot-Py-V2%2Fpy-cord&query=%24.package_version&logo=Discord&label=Pycord&logoColor=white)](https://pycord.dev)
[![Tests Status](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/tests.yaml/badge.svg)](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/tests.yaml)
[![Mypy Status](https://img.shields.io/badge/mypy-checked-%232EBB4E&label=mypy)](https://mypy-lang.org)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://ruff.rs)
[![pre-commit Status](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com)
[![PyMarkdown Status](https://img.shields.io/badge/validated-brightgreen?logo=markdown&label=PyMarkdown)](https://github.com/jackdewinter/pymarkdown)
[![CSS Discord Server](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://cssbham.com/discord)

[TeX-Bot](https://github.com/CSSUoB/TeX-Bot-JS), but back in [Python](https://python.org)!
This is a [Discord bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts) used for managing a community group's [Discord](https://discord.com) [guild](https://discord.com/developers/docs/resources/guild).

Featured in the [CSS Discord guild](https://cssbham.com/discord).

## Terminology

### ["Guild"](https://discord.com/developers/docs/resources/guild) Vs ["Server"](https://wikipedia.org/wiki/Discord#Servers)

Confusingly, [Discord](https://discord.com) uses the term ["guild"](https://discord.com/developers/docs/resources/guild) to refer to a [Discord "server"](https://wikipedia.org/wiki/Discord#Servers), when communicating with developers.
Therefore, the same terminology (["guild"](https://discord.com/developers/docs/resources/guild)) will be used across all documentation in this project.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/guild) & [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#discord.Guild) for more information.)

The term "main guild" is used throughout the code in this repository to refer specifically to your community group's main [Discord guild](https://discord.com/developers/docs/resources/guild).

### "User" Vs "Member" Vs "Guest"

#### [Discord Objects](https://discord.com/developers/docs)

In the context of [Discord](https://discord.com) itself, a ["user"](https://discord.com/developers/docs/resources/user) object represents a [Discord](https://discord.com) account not connected to any specific [guild](https://discord.com/developers/docs/resources/guild).
Therefore, it can be [messaged via DM](https://dictionary.com/browse/dm) or be retrieved via its [snowflake ID](https://discord.com/developers/docs/reference#snowflakes), but little else can be done with it.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/user) & [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#users) for more information.)

In contrast, a [Discord "member" object](https://discord.com/developers/docs/resources/guild#guild-member-object) is a [user](https://discord.com/developers/docs/resources/user) attached to a specific [guild](https://discord.com/developers/docs/resources/guild).
Therefore, it can have [roles](https://discord.com/developers/docs/topics/permissions#role-object), be [banned](https://discord.com/developers/docs/resources/guild#ban-object) & have many other actions applied to it.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/guild#guild-member-object) & [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#discord.Member) for more information.)

#### Community Group Membership

In the context of your community group's membership structure, a "member" is a person that has purchased a membership to join your community group.
This is in contrast to a "guest", which is a person that has not purchased a membership.
Guests often can only attend events that are open to anyone (i.e. **not** members only), and have limited communication/perks within your [Discord guild](https://discord.com/developers/docs/resources/guild).
Some commands may require you to create [roles](https://discord.com/developers/docs/topics/permissions#role-object) within your [Discord guild](https://discord.com/developers/docs/resources/guild), to differentiate between these different types of users.

#### Other Uses

In some other contexts, the term "user" may be used to refer to any person/organisation making use of this project.
(E.g. the description within [the "Error Codes" section](#error-codes).)

## Error Codes

Users of TeX-Bot may encounter an error code when executing a slash-command fails.
If a user encounters any of these errors, please communicate the error to the committee member that has been assigned to upkeep & deployment of your instance of TeX-Bot.
The meaning of each error code is given here:

* `E1011` - The value for the [environment variable](https://wikipedia.org/wiki/Environment_variable) `DISCORD_GUILD_ID` is an [ID](https://discord.com/developers/docs/reference#snowflakes) that references a [Discord guild](https://discord.com/developers/docs/resources/guild) that does not exist

* `E1021` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Committee**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/writeroles`, `/editmessage`, `/induct`, `/strike`, `/archive`, `/kill`, `/delete-all` & `/ensure-members-inducted` [commands](https://discord.com/developers/docs/interactions/application-commands))

* `E1022` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Guest**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/induct`, `/stats`, `/archive` & `/ensure-members-inducted` [commands](https://discord.com/developers/docs/interactions/application-commands))

* `E1023` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Member**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/makemember` & `/ensure-members-inducted` [commands](https://discord.com/developers/docs/interactions/application-commands))

* `E1024` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Archivist**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/archive` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1025` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Applicant**". (This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/make-applicant` [command](https://discord.com/developers/docs/interactions/application-commands) and respective user and message commands)

* `E1026` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-objec) with the name "@**Committee-Elect**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/handover` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1031` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) with the name "#**roles**".
(This [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) is required for the `/writeroles` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1032` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) with the name "#**general**".
(This [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) is required for the `/induct` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1041` - The community group member IDs could not be retrieved from the `MEMBERS_LIST_URL`.
(It is likely that your `MEMBERS_LIST_URL_SESSION_COOKIE` is invalid.
If your community group is a [Guild of Students](https://guildofstudents.com) [society](https://wikipedia.org/wiki/Student_society), the community group member IDs will be a list of [UoB IDs](https://intranet.birmingham.ac.uk/campus-services/id-cards.aspx))

* `E1042` - The reference to the `@everyone` [role](https://discord.com/developers/docs/topics/permissions#role-object) could not be correctly retrieved.
Try running the command that caused this error again.
If the error persists, please file an issue on [this project's bug tracker](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues), including the details of what command was run to create this error

* `E1043` - A button callback interaction did not contain the related [user](https://discord.com/developers/docs/resources/user).
Try pressing the button that caused this error again.
If the error persists, please file an issue on [this project's bug tracker](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues), including the details of what command was run to create this error

* `E1044` - An interaction was denied because the Discord permissions for TeX-Bot were not set correctly

## Log-Entry Error Levels

When an error occurs, a log entry will be created.
One of these possible error levels will be associated with that log entry.
Below are the explanations of what effects/causes each log-level represents:

* `WARNING` - An error occurred that did ***not* result in any failure to complete the current request/interaction**.
However, some minor inconsistencies/data loss may have occurred.
This may require some changes to the deployment configuration or [an issue about a bug to be raised](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues)

* `ERROR` - The current **request/interaction could *not* be completed** due to a major error.
The problem that caused the error should be addressed *immediately*, or otherwise TeX-Bot should be manually shut down to prevent further errors

* `CRITICAL` - An **unrecoverable error occurred**.
This level of error will cause TeX-Bot to shut down, as the problem can only be solved by fixing one or more of the [configuration environment variables](https://wikipedia.org/wiki/Environment_variable)

## [Repeated Tasks](https://docs.pycord.dev/en/stable/ext/tasks) Conditions

The [configuration variables](https://wikipedia.org/wiki/Environment_variable) `SEND_INTRODUCTION_REMINDERS` & `SEND_GET_ROLES_REMINDERS` determine whether their related [tasks](https://docs.pycord.dev/en/stable/ext/tasks) should run.
However, because these are rather annoying/drastic actions to be executed automatically, there are additional conditions that must be met on a per-[member](https://discord.com/developers/docs/resources/guild#guild-member-object) basis for the action to trigger.
The conditions for each [task](https://docs.pycord.dev/en/stable/ext/tasks) are listed below, along with the additional [environment variables](https://wikipedia.org/wiki/Environment_variable) that can be used to configure the conditions to suit your needs.

| Task Name               | Enable/Disable                                                                                                                                                                                                                                                                | Per-Member Conditions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Scheduled Interval                                                                                                                                                                                                                                                                                                                                                                  |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `introduction_reminder` | `SEND_INTRODUCTION_REMINDERS`:<br/>* `Once` - Only send the introduction reminder once (even if they later delete the message)<br/>* `Interval` - Send an introduction reminder at a set interval<br/>* `False` - Do not send introduction reminders                          | * The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not been inducted (does not have the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object))<br/>* The time since the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) joined your community's guild is greater than `SEND_INTRODUCTION_REMINDERS_DELAY`<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not opted out of introduction reminders<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not yet been sent an introduction reminder. (Only applies when `SEND_INTRODUCTION_REMINDERS` is set to the value `Once`)                                                                                   | The interval of time between this task running is determined by `SEND_INTRODUCTION_REMINDERS_INTERVAL`. (When `SEND_INTRODUCTION_REMINDERS` is set to the value `Once`, all [Discord members](https://discord.com/developers/docs/resources/guild#guild-member-object) will still be checked at this interval, just not sent a message if they have already been sent an introduction reminder). The default interval is to send messages every 6 hours |
| `get_roles_reminder`    | `SEND_GET_ROLES_REMINDERS`:<br/>* `True` - A single reminder for the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) will be sent to them only once (even if they later delete the message)<br/>* `False` - Do not send any reminders for [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) | * The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has been inducted (has the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object))<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) does not have any of the opt-in [roles](https://discord.com/developers/docs/topics/permissions#role-object). (E.g. "@**First Year**" or "@**Anime**".) (Having the green "@**Member**" [role](https://discord.com/developers/docs/topics/permissions#role-object) or even the "@**Committee**" [role](https://discord.com/developers/docs/topics/permissions#role-object) makes no difference)<br/>* The time since the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) was inducted (gained the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object)) is greater than `SEND_GET_ROLES_REMINDERS_DELAY`<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not yet been sent a reminder to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) | The interval of time between this task running is determined by `ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL`. It is unlikely that this value will need to be changed from the default of 24 hours                                                                                                                                                                                   |

## Deploying in Production

The only supported way to deploy TeX-Bot in production is by using our pre-built [docker container](https://docs.docker.com/resources/what-container).
It is [built automatically](.github/workflows/update-container-image.yaml) when new changes are made to [the `main` branch](https://github.com/CSSUoB/TeX-Bot-Py-V2/tree/main), and can be pulled from the [GitHub Container Registry](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry) with this identifier: [`ghcr.io/CSSUoB/tex-bot-py-v2:latest`](https://github.com/CSSUoB/TeX-Bot-Py-V2/pkgs/container/tex-bot-py-v2).
(An introduction on how to use a [docker-compose deployment](https://docs.docker.com/compose) can be found [here](https://docs.docker.com/get-started/08_using_compose).)

Before running the [container](https://docs.docker.com/resources/what-container), some [environment variables](https://wikipedia.org/wiki/Environment_variable) will need to be set.
These can be defined in your [`compose.yaml`](https://docs.docker.com/compose/compose-application-model#the-compose-file) file.
The required [environment variables](https://wikipedia.org/wiki/Environment_variable) are explained within [the "Setting Environment Variables" section](#setting-environment-variables).

## Local Deployment

### Installing Dependencies

1. Ensure that you have [Poetry](https://python-poetry.org) installed
2. Navigate to this project's repository root folder
3. To install the required dependencies, execute the following command:

```shell
poetry install --no-root --sync
```

* The [`--no-root` flag](https://python-poetry.org/docs/cli#options-2) installs the dependencies without installing the [root project](https://packaging.python.org/glossary#term-Project) as a [package](https://packaging.python.org/glossary#term-Distribution-Package).
[Poetry](https://python-poetry.org) attempts to install the [project](https://packaging.python.org/glossary#term-Project) as a [package](https://packaging.python.org/glossary#term-Distribution-Package) by default because [Poetry](https://python-poetry.org) is often used to develop [library packages](https://packaging.python.org/glossary#term-Distribution-Package), which need to be installed themselves.

* The [`--sync` flag](https://python-poetry.org/docs/cli#options-2) uninstalls any additional [packages](https://packaging.python.org/glossary#term-Distribution-Package) that have already been installed in the [local environment](https://packaging.python.org/glossary#term-Virtual-Environment), but are not required in the [`pyproject.toml`](pyproject.toml)

### Activating the [Poetry](https://python-poetry.org) [Environment](https://packaging.python.org/glossary#term-Virtual-Environment)

To use the installed dependencies, the [environment](https://packaging.python.org/glossary#term-Virtual-Environment) they were installed within must be activated.
The easiest way to do this (as described by [Poetry's guide](https://python-poetry.org/docs/basic-usage#activating-the-virtual-environment)) is with the below command:

```shell
poetry shell
```

If you do not want to activate the [virtual environment](https://packaging.python.org/glossary#term-Virtual-Environment), every [command](https://wikipedia.org/wiki/Command-line_interface#Anatomy_of_a_shell_CLI) can be run prepended with [`poetry run`](https://python-poetry.org/docs/cli#run), to run the given [command](https://wikipedia.org/wiki/Command-line_interface#Anatomy_of_a_shell_CLI) within the [Poetry context](https://python-poetry.org/docs/basic-usage#activating-the-virtual-environment).
(Every [command](https://wikipedia.org/wiki/Command-line_interface#Anatomy_of_a_shell_CLI) within the documentation within this project will include the [`poetry run`](https://python-poetry.org/docs/cli#run) prefix for convenience.
**It can be excluded if you have already [activated the virtual environment](https://python-poetry.org/docs/basic-usage#activating-the-virtual-environment).**)

### Creating Your [Bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)

A full guide on how to create your bot's account can be found [here; on Pycord's wiki](https://docs.pycord.dev/en/stable/discord.html).

You'll need to create a [Discord bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts) of your own in the [Discord Developer Portal](https://discord.com/developers/applications).
It's also handy if you have an empty [guild](https://discord.com/developers/docs/resources/guild) for you to test in.

You can retrieve the correct [invite URL](https://docs.pycord.dev/en/stable/discord.html#inviting-your-bot) to use by navigating to the root folder, then running the following command:

```shell
poetry run python -m utils generate_invite_url {discord_bot_application_id} {discord_guild_id}
```

* `{discord_bot_application_id}` must be replaced by the [application ID](https://discord.com/developers/applications) of your [bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)

* `{discord_guild_id}` must be replaced by the [snowflake ID](https://discord.com/developers/docs/reference#snowflakes) of your community group's [guild](https://discord.com/developers/docs/resources/guild)

### Setting [Environment Variables](https://wikipedia.org/wiki/Environment_variable)

You'll also need to set a number of [environment variables](https://wikipedia.org/wiki/Environment_variable) before running TeX-Bot:

* `DISCORD_BOT_TOKEN`: The [secret token](https://itexus.com/glossary/discord-bot-token) for the [instance of TeX-Bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts) you created.
(The [token](https://itexus.com/glossary/discord-bot-token) is available on [your bot page in the Developer Portal](https://discord.com/developers/applications).)

* `DISCORD_GUILD_ID`: The [ID](https://discord.com/developers/docs/reference#snowflakes) of your community group's [Discord guild](https://discord.com/developers/docs/resources/guild).

* `DISCORD_LOG_CHANNEL_WEBHOOK_URL`: The [webhook URL](https://support.discord.com/hc/articles/228383668-Intro-to-Webhooks) of the [Discord text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) where error log messages should be sent.
(This setting is optional.
Error logs will **always** be sent to the [console](https://wikipedia.org/wiki/Terminal_emulator), this setting allows them to also be sent to a [Discord log channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel).)

* `ORGANISATION_ID`: Your Guild society ID. This is used to dynamically create the members list among other needed URLs.

* `MEMBERS_LIST_URL_SESSION_COOKIE`: The members-list [URL](https://wikipedia.org/wiki/URL) [session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie).
(If your group's members-list is stored at a [URL](https://wikipedia.org/wiki/URL) that requires [authentication](https://wikipedia.org/wiki/Authentication), this [session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie) should [authenticate](https://wikipedia.org/wiki/Authentication) TeX-Bot to view your group's members-list, as if it were [logged in to the website](https://wikipedia.org/wiki/Login_session) as a Committee member.
This can be [extracted from your web-browser](https://wikihow.com/View-Cookies), after logging in to view your members-list yourself.
It will probably be listed as a [cookie](https://wikipedia.org/wiki/HTTP_cookie) named [`.ASPXAUTH`](https://stackoverflow.com/a/424061/14403974).)

You can put these [variables](https://wikipedia.org/wiki/Environment_variable) in a [`.env` file](https://blog.bitsrc.io/a-gentle-introduction-to-env-files-9ad424cc5ff4) in the root folder, as [python-dotenv](https://saurabh-kumar.com/python-dotenv) is used to collect all [environment variables](https://wikipedia.org/wiki/Environment_variable).
There is an [`.env.example` file](.env.example) in the repo that you can rename and populate.

There are also many other configuration settings that can be changed to alter the behaviour of TeX-Bot.
These are all listed in [the `.env.example` file](.env.example), along with the behaviours that will be affected.

Any [variables](https://wikipedia.org/wiki/Environment_variable), in [the `.env.example` file](.env.example), marked with `# !!REQUIRED!!` must be set before running TeX-Bot.
All other [variables](https://wikipedia.org/wiki/Environment_variable) are optional and their default values are shown as the example value for each variable in [the `.env.example` file](.env.example).

### Running The Bot

Once everything is set up, you should be able to execute the following command to automatically run TeX-Bot & connect it to your [Discord guild](https://discord.com/developers/docs/resources/guild):

```shell
poetry run python -m main
```

## Contributing

Contributions are welcome!

If you want to contribute, please [create](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) a [pull request](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests), and we'll review, test and (likely) merge it.
Please comment on any [issues](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues) you'd like to work on, to prevent duplication of work.
If you find any bugs/problems or have any feature suggestions, please [create](https://docs.github.com/issues/tracking-your-work-with-issues/creating-an-issue) an [issue](https://docs.github.com/issues/tracking-your-work-with-issues/about-issues).

Before making contributions, it is highly suggested that you read [`CONTRIBUTING.md`](CONTRIBUTING.md).
This will ensure your code meets the standard required for this project and gives you the greatest chances of your contributions being merged.
