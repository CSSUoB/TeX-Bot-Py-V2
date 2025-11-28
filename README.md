# TeX-Bot-Py-V2

[![Python Version](https://img.shields.io/badge/Python-3.13-blue?&logo=Python&logoColor=white)](https://python.org/downloads/release/python-3139)
[![Pycord Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Ftoml-version-finder.carrotmanmatt.com%2Flock%2FCSSUoB%2FTeX-Bot-Py-V2%2Fpy-cord&query=%24.package_version&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM6dj0iaHR0cHM6Ly92ZWN0YS5pby9uYW5vIj48cGF0aCBkPSJNMTQuMjUuMThsLjkuMi43My4yNi41OS4zLjQ1LjMyLjM0LjM0LjI1LjM0LjE2LjMzLjEuMy4wNC4yNi4wMi4yLS4wMS4xM1Y4LjVsLS4wNS42My0uMTMuNTUtLjIxLjQ2LS4yNi4zOC0uMy4zMS0uMzMuMjUtLjM1LjE5LS4zNS4xNC0uMzMuMS0uMy4wNy0uMjYuMDQtLjIxLjAySDguNzdsLS42OS4wNS0uNTkuMTQtLjUuMjItLjQxLjI3LS4zMy4zMi0uMjcuMzUtLjIuMzYtLjE1LjM3LS4xLjM1LS4wNy4zMi0uMDQuMjctLjAyLjIxdjMuMDZIMy4xN2wtLjIxLS4wMy0uMjgtLjA3LS4zMi0uMTItLjM1LS4xOC0uMzYtLjI2LS4zNi0uMzYtLjM1LS40Ni0uMzItLjU5LS4yOC0uNzMtLjIxLS44OC0uMTQtMS4wNS0uMDUtMS4yMy4wNi0xLjIyLjE2LTEuMDQuMjQtLjg3LjMyLS43MS4zNi0uNTcuNC0uNDQuNDItLjMzLjQyLS4yNC40LS4xNi4zNi0uMS4zMi0uMDUuMjQtLjAxaC4xNmwuMDYuMDFoOC4xNnYtLjgzSDYuMThsLS4wMS0yLjc1LS4wMi0uMzcuMDUtLjM0LjExLS4zMS4xNy0uMjguMjUtLjI2LjMxLS4yMy4zOC0uMi40NC0uMTguNTEtLjE1LjU4LS4xMi42NC0uMS43MS0uMDYuNzctLjA0Ljg0LS4wMiAxLjI3LjA1IDEuMDcuMTN6bS02LjMgMS45OGwtLjIzLjMzLS4wOC40MS4wOC40MS4yMy4zNC4zMy4yMi40MS4wOS40MS0uMDkuMzMtLjIyLjIzLS4zNC4wOC0uNDEtLjA4LS40MS0uMjMtLjMzLS4zMy0uMjItLjQxLS4wOS0uNDEuMDktLjMzLjIyeiIgZmlsbD0iIzVlNmRmMCIvPjxwYXRoIGQ9Ik0xNC41NyAyMC4zNmwtLjIzLjMzLS4wOC40MS4wOC40MS4yMy4zMy4zMy4yMy40MS4wOC40MS0uMDguMzMtLjIzLjIzLS4zMy4wOC0uNDEtLjA4LS40MS0uMjMtLjMzLS4zMy0uMjMtLjQxLS4wOC0uNDEuMDgtLjMzLjIzem02LjQ3LTE0LjI1bC4yOC4wNi4zMi4xMi4zNS4xOC4zNi4yNy4zNi4zNS4zNS40Ny4zMi41OS4yOC43My4yMS44OC4xNCAxLjA0LjA1IDEuMjMtLjA2IDEuMjMtLjE2IDEuMDQtLjI0Ljg2LS4zMi43MS0uMzYuNTctLjQuNDUtLjQyLjMzLS40Mi4yNC0uNC4xNi0uMzYuMDktLjMyLjA1LS4yNC4wMi0uMTYtLjAxaC04LjIydi44Mmg1Ljg0bC4wMSAyLjc2LjAyLjM2LS4wNS4zNC0uMTEuMzEtLjE3LjI5LS4yNS4yNS0uMzEuMjQtLjM4LjItLjQ0LjE3LS41MS4xNS0uNTguMTMtLjY0LjA5LS43MS4wNy0uNzcuMDQtLjg0LjAxLTEuMjctLjA0LTEuMDctLjE0LS45LS4yLS43My0uMjUtLjU5LS4zLS40NS0uMzMtLjM0LS4zNC0uMjUtLjM0LS4xNi0uMzMtLjEtLjMtLjA0LS4yNS0uMDItLjIuMDEtLjEzdi01LjM0bC4wNS0uNjQuMTMtLjU0LjIxLS40Ni4yNi0uMzguMy0uMzIuMzMtLjI0LjM1LS4yLjM1LS4xNC4zMy0uMS4zLS4wNi4yNi0uMDQuMjEtLjAyLjEzLS4wMWg1Ljg0bC42OS0uMDUuNTktLjE0LjUtLjIxLjQxLS4yOC4zMy0uMzIuMjctLjM1LjItLjM2LjE1LS4zNi4xLS4zNS4wNy0uMzIuMDQtLjI4LjAyLS4yMVY2LjA3aDIuMDlsLjE0LjAxLjIxLjAzeiIgZmlsbD0iI2Q0ZDRkNCIvPjwvc3ZnPg==&label=Pycord)](https://pycord.dev)
[![Tests Status](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/check-build-deploy.yaml/badge.svg)](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/check-build-deploy.yaml)
[![Mypy Status](https://img.shields.io/badge/mypy-checked-%232EBB4E&label=mypy)](https://mypy-lang.org)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://ruff.rs)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://astral.sh/uv)
[![pre-commit Status](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com)
[![PyMarkdown Status](https://img.shields.io/badge/validated-brightgreen?logo=markdown&label=PyMarkdown)](https://github.com/jackdewinter/pymarkdown)
[![CSS Discord Server](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://cssbham.com/discord)

TeX-Bot, but back in [Python](https://python.org)!
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

## Error Codes

Members of your [Discord guild](https://discord.com/developers/docs/resources/guild) using TeX-Bot may encounter an error code when executing a slash-command fails.
If a user encounters any of these errors, please communicate the error to the committee member that has been assigned to upkeep & deployment of your instance of TeX-Bot.
The meaning of each error code is given here:

* `E1011` - The value for the [environment variable](https://wikipedia.org/wiki/Environment_variable) `DISCORD_GUILD_ID` is an [ID](https://discord.com/developers/docs/reference#snowflakes) that references a [Discord guild](https://discord.com/developers/docs/resources/guild) that does not exist

* `E1021` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Committee**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/write-roles`, `/edit-message`, `/induct`, `/strike`, `/archive`, `/kill`, `/delete-all` & `/ensure-members-inducted` [commands](https://discord.com/developers/docs/interactions/application-commands))

* `E1022` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Guest**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/induct`, `/stats`, `/archive` & `/ensure-members-inducted` [commands](https://discord.com/developers/docs/interactions/application-commands))

* `E1023` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Member**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/make-member` & `/ensure-members-inducted` [commands](https://discord.com/developers/docs/interactions/application-commands))

* `E1024` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Archivist**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/archive` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1025` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Applicant**". (This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/make-applicant` [command](https://discord.com/developers/docs/interactions/application-commands) and respective user and message commands)

* `E1026` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-objec) with the name "@**Committee-Elect**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/handover` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1031` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) with the name "#**roles**".
(This [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) is required for the `/writeroles` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1032` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) with the name "#**general**".
(This [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) is required for the `/induct` [command](https://discord.com/developers/docs/interactions/application-commands))

* `E1041` - The community group member IDs could not be retrieved from the SU platform.
(It is likely that your `SU_PLATFORM_ACCESS_COOKIE` is invalid.
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
It is can be pulled from the [GitHub Container Registry](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry) with this identifier: [`ghcr.io/CSSUoB/tex-bot-py-v2:latest`](https://github.com/CSSUoB/TeX-Bot-Py-V2/pkgs/container/tex-bot-py-v2).
(An introduction on how to use a [docker-compose deployment](https://docs.docker.com/compose) can be found [here](https://docs.docker.com/get-started/08_using_compose).)
See [**Versioning**](#versioning) for the full list of available version tags for each release.

Before running the [container](https://docs.docker.com/resources/what-container), some [environment variables](https://wikipedia.org/wiki/Environment_variable) will need to be set.
These can be defined in your [`compose.yaml`](https://docs.docker.com/compose/compose-application-model#the-compose-file) file.
The required [environment variables](https://wikipedia.org/wiki/Environment_variable) are explained within [the "Setting Environment Variables" section](#setting-environment-variables).

## Local Deployment

### Installing Dependencies

1. Ensure that you have [uv](https://docs.astral.sh/uv/getting-started/installation) installed
2. Navigate to this project's repository root folder
3. To install the required dependencies, execute the following command:

```shell
uv sync
```

> [!TIP]
> Syncing the dependencies is not required. uv performs this automatically every time the `uv run` command is used

### Creating Your [Bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)

A full guide on how to create your bot's account can be found [here; on Pycord's wiki](https://docs.pycord.dev/en/stable/discord.html).

You'll need to create a [Discord bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts) of your own in the [Discord Developer Portal](https://discord.com/developers/applications).
It's also handy if you have an empty [Discord guild](https://discord.com/developers/docs/resources/guild) for you to test in.

The correct [invite URL](https://docs.pycord.dev/en/stable/discord.html#inviting-your-bot) will be displayed to you in the console the first time you run the bot (or if you set a high verbosity log level)

### Setting [Environment Variables](https://wikipedia.org/wiki/Environment_variable)

You'll also need to set a number of [environment variables](https://wikipedia.org/wiki/Environment_variable) before running TeX-Bot:

* `DISCORD_BOT_TOKEN`: The [Discord bot secret token](https://itexus.com/glossary/discord-bot-token) for the [instance of TeX-Bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts) you created.
  * The [Discord bot token](https://itexus.com/glossary/discord-bot-token) is available on [your bot's page in the Discord Developer Portal](https://discord.com/developers/applications).

* `DISCORD_GUILD_ID`: The [ID](https://discord.com/developers/docs/reference#snowflakes) of your community group's [Discord guild](https://discord.com/developers/docs/resources/guild).

* `DISCORD_LOG_CHANNEL_WEBHOOK_URL`: The [webhook URL](https://support.discord.com/hc/articles/228383668-Intro-to-Webhooks) of the [Discord text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) where error log messages should be sent.
  * This setting is optional.
    Error logs will **always** be sent to the [console](https://wikipedia.org/wiki/Terminal_emulator), this setting just allows them to also be sent to a [Discord log channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel).

* `ORGANISATION_ID`: Your SU platform organisation ID. This is used to dynamically create the members list and other needed URLs.

* `SU_PLATFORM_ACCESS_COOKIE`: The SU platform [access session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie).
  * This [session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie) will [authenticate](https://wikipedia.org/wiki/Authentication) TeX-Bot to view your group's members list on the SU platform, as if it were [logged in to the website](https://wikipedia.org/wiki/Login_session) as a Committee member.
  * This can be [extracted from your web-browser](https://wikihow.com/View-Cookies), after logging in to view your members list yourself.
    It will most likely be listed as a [cookie](https://wikipedia.org/wiki/HTTP_cookie) named `.AspNet.SharedCookie`.
  * If you wish to test TeX-Bot with the SU platform-access disabled, a dummy value of 128 `0` characters can be used.
    Note that this will cause many commands and scheduled tasks to fail when they are used at runtime.

You can put these [variables](https://wikipedia.org/wiki/Environment_variable) in a [`.env` file](https://blog.bitsrc.io/a-gentle-introduction-to-env-files-9ad424cc5ff4) in the root folder, as [python-dotenv](https://saurabh-kumar.com/python-dotenv) is used to collect all [environment variables](https://wikipedia.org/wiki/Environment_variable).
There is an [`.env.example` file](.env.example) in the repo that you can rename and populate.

There are also many other configuration settings that can be changed to alter the behaviour of TeX-Bot.
These are all listed in [the `.env.example` file](.env.example), along with the behaviours that will be affected.

Any [variables](https://wikipedia.org/wiki/Environment_variable), in [the `.env.example` file](.env.example), marked with `# !!REQUIRED!!` must be set before running TeX-Bot.
All other [variables](https://wikipedia.org/wiki/Environment_variable) are optional and their default values are shown as the example value for each variable in [the `.env.example` file](.env.example).

### Running The Bot

Once everything is set up, you should be able to execute the following command to automatically run TeX-Bot & connect it to your [Discord guild](https://discord.com/developers/docs/resources/guild):

```shell
uv run -m main
```

## Contributing

Contributions are welcome!

If you want to contribute, please [create](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) a [pull request](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests), and we'll review, test and (likely) merge it.
Please comment on any [issues](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues) you'd like to work on, to prevent duplication of work.
If you find any bugs/problems or have any feature suggestions, please [create](https://docs.github.com/issues/tracking-your-work-with-issues/creating-an-issue) an [issue](https://docs.github.com/issues/tracking-your-work-with-issues/about-issues).

Before making contributions, it is highly suggested that you read [`CONTRIBUTING.md`](CONTRIBUTING.md).
This will ensure your code meets the standard required for this project and gives you the greatest chances of your contributions being merged.

## Versioning

This project follows the [semantic versioning scheme](https://semver.org).
We currently treat TeX-Bot as alpha software, and as such no numbered release has been made yet.

When selecting a version tag to use for [deploying TeX-Bot as a container image](#deploying-in-production) there are multiple tag schemes available:

* `latest` - The most recent numerically tagged version released
* `br-<branch>` - The most recent commit from a given branch in this repository (E.g. `br-main`) (N.B. this does not include branches of forks of this repository)
* `v<major>` - The most recent tagged version released with a specific major version (E.g. `v4` could map to the git tag `v4.1.6` or `v4.0.0`)
* `<major>.<minor>` - The most recent tagged version released with a specific minor and major version (E.g. `4.1` could map to the git tag `v4.1.0` or `v4.1.6`)
* `<major>.<minor>.<patch>` - A specific tagged version (E.g. `4.1.6` maps to the git tag `v4.1.6` only)
* `pr-<pr-number>` - The most recent commit from a branch in a specific pull request (E.g. `pr-420`) (N.B this **will** work for pull requests that come from forks of this repository)

The only supported version of TeX-Bot is the most recent numbered release (if it exists).
When submitting a bug report/feature request, we may ask you to upgrade the most recent version before we consider validating your report.
We have no backporting policy at present.

To create a new tagged release, create a single git tag matching the full version number, prefixed by a `v` character, on the most recent commit on the main branch (E.g. `v4.1.6`).
This will initiate the GitHub workflow to generate all the matching container image tags.
