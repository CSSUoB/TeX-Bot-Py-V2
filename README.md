# TeX-Bot-Py-V2

[![Python Version](https://img.shields.io/badge/Python-3.13-blue?&logo=Python&logoColor=white)](https://python.org/downloads/release/python-3139)
[![Pycord Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Ftoml-version-finder.carrotmanmatt.com%2Flock%2FCSSUoB%2FTeX-Bot-Py-V2%2Fpy-cord&query=%24.package_version&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM6dj0iaHR0cHM6Ly92ZWN0YS5pby9uYW5vIj48cGF0aCBkPSJNMTQuMjUuMThsLjkuMi43My4yNi41OS4zLjQ1LjMyLjM0LjM0LjI1LjM0LjE2LjMzLjEuMy4wNC4yNi4wMi4yLS4wMS4xM1Y4LjVsLS4wNS42My0uMTMuNTUtLjIxLjQ2LS4yNi4zOC0uMy4zMS0uMzMuMjUtLjM1LjE5LS4zNS4xNC0uMzMuMS0uMy4wNy0uMjYuMDQtLjIxLjAySDguNzdsLS42OS4wNS0uNTkuMTQtLjUuMjItLjQxLjI3LS4zMy4zMi0uMjcuMzUtLjIuMzYtLjE1LjM3LS4xLjM1LS4wNy4zMi0uMDQuMjctLjAyLjIxdjMuMDZIMy4xN2wtLjIxLS4wMy0uMjgtLjA3LS4zMi0uMTItLjM1LS4xOC0uMzYtLjI2LS4zNi0uMzYtLjM1LS40Ni0uMzItLjU5LS4yOC0uNzMtLjIxLS44OC0uMTQtMS4wNS0uMDUtMS4yMy4wNi0xLjIyLjE2LTEuMDQuMjQtLjg3LjMyLS43MS4zNi0uNTcuNC0uNDQuNDItLjMzLjQyLS4yNC40LS4xNi4zNi0uMS4zMi0uMDUuMjQtLjAxaC4xNmwuMDYuMDFoOC4xNnYtLjgzSDYuMThsLS4wMS0yLjc1LS4wMi0uMzcuMDUtLjM0LjExLS4zMS4xNy0uMjguMjUtLjI2LjMxLS4yMy4zOC0uMi40NC0uMTguNTEtLjE1LjU4LS4xMi42NC0uMS43MS0uMDYuNzctLjA0Ljg0LS4wMiAxLjI3LjA1IDEuMDcuMTN6bS02LjMgMS45OGwtLjIzLjMzLS4wOC40MS4wOC40MS4yMy4zNC4zMy4yMi40MS4wOS40MS0uMDkuMzMtLjIyLjIzLS4zNC4wOC0uNDEtLjA4LS40MS0uMjMtLjMzLS4zMy0uMjItLjQxLS4wOS0uNDEuMDktLjMzLjIyeiIgZmlsbD0iIzVlNmRmMCIvPjxwYXRoIGQ9Ik0xNC41NyAyMC4zNmwtLjIzLjMzLS4wOC40MS4wOC40MS4yMy4zMy4zMy4yMy40MS4wOC40MS0uMDguMzMtLjIzLjIzLS4zMy4wOC0uNDEtLjA4LS40MS0uMjMtLjMzLS4zMy0uMjMtLjQxLS4wOC0uNDEuMDgtLjMzLjIzem02LjQ3LTE0LjI1bC4yOC4wNi4zMi4xMi4zNS4xOC4zNi4yNy4zNi4zNS4zNS40Ny4zMi41OS4yOC43My4yMS44OC4xNCAxLjA0LjA1IDEuMjMtLjA2IDEuMjMtLjE2IDEuMDQtLjI0Ljg2LS4zMi43MS0uMzYuNTctLjQuNDUtLjQyLjMzLS40Mi4yNC0uNC4xNi0uMzYuMDktLjMyLjA1LS4yNC4wMi0uMTYtLjAxaC04LjIydi44Mmg1Ljg0bC4wMSAyLjc2LjAyLjM2LS4wNS4zNC0uMTEuMzEtLjE3LjI5LS4yNS4yNS0uMzEuMjQtLjM4LjItLjQ0LjE3LS41MS4xNS0uNTguMTMtLjY0LjA5LS43MS4wNy0uNzcuMDQtLjg0LjAxLTEuMjctLjA0LTEuMDctLjE0LS45LS4yLS43My0uMjUtLjU5LS4zLS40NS0uMzMtLjM0LS4zNC0uMjUtLjM0LS4xNi0uMzMtLjEtLjMtLjA0LS4yNS0uMDItLjIuMDEtLjEzdi01LjM0bC4wNS0uNjQuMTMtLjU0LjIxLS40Ni4yNi0uMzguMy0uMzIuMzMtLjI0LjM1LS4yLjM1LS4xNC4zMy0uMS4zLS4wNi4yNi0uMDQuMjEtLjAyLjEzLS4wMWg1Ljg0bC42OS0uMDUuNTktLjE0LjUtLjIxLjQxLS4yOC4zMy0uMzIuMjctLjM1LjItLjM2LjE1LS4zNi4xLS4zNS4wNy0uMzIuMDQtLjI4LjAyLS4yMVY2LjA3aDIuMDlsLjE0LjAxLjIxLjAzeiIgZmlsbD0iI2Q0ZDRkNCIvPjwvc3ZnPg==&label=Pycord)](https://pycord.dev)
[![Tests Status](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/check-build-deploy.yaml/badge.svg)](https://github.com/CSSUoB/TeX-Bot-Py-V2/actions/workflows/check-build-deploy.yaml)
[![mypy Status](https://img.shields.io/badge/mypy-checked-%232EBB4E&label=mypy)](https://mypy-lang.org)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://ruff.rs)
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

* `E1011` - The value of the `discord:main-guild-id` [configuration setting](#configuring-tex-bot) is an [ID](https://discord.com/developers/docs/reference#snowflakes) that references a [Discord guild](https://discord.com/developers/docs/resources/guild) that does not exist

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
(It is likely that your `community-group:msl:auth-cookie` [configuration setting](#configuring-tex-bot) is invalid.
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
This level of error will cause TeX-Bot to shut down, as the problem can only be solved by fixing one or more of the settings within [your deployment configuration file](#configuring-tex-bot)

## [Repeated Tasks](https://docs.pycord.dev/en/stable/ext/tasks) Conditions

The `reminders:send-introduction-reminders:enabled` & `reminders:send-get-roles-reminders:enabled` [configuration settings](#configuring-tex-bot) determine whether their related [tasks](https://docs.pycord.dev/en/stable/ext/tasks) should run.
However, because these are rather annoying/drastic actions to be executed automatically, there are additional conditions that must be met on a per-[member](https://discord.com/developers/docs/resources/guild#guild-member-object) basis for the action to trigger.
The conditions for each [task](https://docs.pycord.dev/en/stable/ext/tasks) are listed below, along with the additional settings that can be used to configure the conditions to suit your needs.

> [!IMPORTANT]
> Whether each task is enabled, and the interval it runs at, are fixed when the task is created as TeX-Bot starts up.
> Changing either of them requires TeX-Bot to be restarted; `/config reload` will tell you so.
> The `delay` settings are read each time they are used, so they take effect immediately.

| Task Name               | Enable/Disable                                                                                                                                                                                                                                                                | Per-Member Conditions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Scheduled Interval                                                                                                                                                                                                                                                                                                                                                                  |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `introduction_reminder` | `reminders:send-introduction-reminders:enabled`:<br/>* `once` - Only send the introduction reminder once (even if they later delete the message)<br/>* `interval` - Send an introduction reminder at a set interval<br/>* `false` - Do not send introduction reminders                          | * The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not been inducted (does not have the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object))<br/>* The time since the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) joined your community's guild is greater than `reminders:send-introduction-reminders:delay`<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not opted out of introduction reminders<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not yet been sent an introduction reminder. (Only applies when `reminders:send-introduction-reminders:enabled` is set to the value `once`)                                                                                   | The interval of time between this task running is determined by `reminders:send-introduction-reminders:interval`. (When `reminders:send-introduction-reminders:enabled` is set to the value `once`, all [Discord members](https://discord.com/developers/docs/resources/guild#guild-member-object) will still be checked at this interval, just not sent a message if they have already been sent an introduction reminder). The default interval is to send messages every 6 hours |
| `get_roles_reminder`    | `reminders:send-get-roles-reminders:enabled`:<br/>* `true` - A single reminder for the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) will be sent to them only once (even if they later delete the message)<br/>* `false` - Do not send any reminders for [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) | * The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has been inducted (has the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object))<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) does not have any of the opt-in [roles](https://discord.com/developers/docs/topics/permissions#role-object). (E.g. "@**First Year**" or "@**Anime**".) (Having the green "@**Member**" [role](https://discord.com/developers/docs/topics/permissions#role-object) or even the "@**Committee**" [role](https://discord.com/developers/docs/topics/permissions#role-object) makes no difference)<br/>* The time since the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) was inducted (gained the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object)) is greater than `reminders:send-get-roles-reminders:delay`<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not yet been sent a reminder to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) | The interval of time between this task running is determined by `reminders:send-get-roles-reminders:interval`. It is unlikely that this value will need to be changed from the default of every 6 hours                                                                                                                                                                                   |

## Deploying in Production

The only supported way to deploy TeX-Bot in production is by using our pre-built [docker container](https://docs.docker.com/resources/what-container).
It is can be pulled from the [GitHub Container Registry](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry) with this identifier: [`ghcr.io/CSSUoB/tex-bot-py-v2:latest`](https://github.com/CSSUoB/TeX-Bot-Py-V2/pkgs/container/tex-bot-py-v2).
(An introduction on how to use a [docker-compose deployment](https://docs.docker.com/compose) can be found [here](https://docs.docker.com/get-started/08_using_compose).)
See [**Versioning**](#versioning) for the full list of available version tags for each release.

Before running the [container](https://docs.docker.com/resources/what-container), you will need to create a deployment configuration file.
This is explained within [the "Configuring TeX-Bot" section](#configuring-tex-bot).

The container reads its configuration from `/app/data/tex-bot-deployment.yaml`, so mount the **directory** holding your configuration file at `/app/data`:

```yaml
services:
  tex-bot:
    image: ghcr.io/cssuob/tex-bot-py-v2:latest
    volumes:
      - ./tex-bot-data:/app/data
```

> [!IMPORTANT]
> Mount the directory, rather than the configuration file itself.
> TeX-Bot rewrites the file in place whenever [the `/config` command](#changing-settings-from-within-discord) changes a setting, and an individually mounted file cannot be replaced.

The container runs as the non-root user with UID & GID `999`, which must be able to read and write your configuration file:

```shell
chown -R 999:999 ./tex-bot-data
```

To keep your configuration somewhere else within the container, set the `TEX_BOT_CONFIG_PATH` [environment variable](https://wikipedia.org/wiki/Environment_variable) to the full path of the file.

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

### Configuring TeX-Bot

TeX-Bot is configured by a single [YAML](https://yaml.org) file, `tex-bot-deployment.yaml`.
Copy [the example file](tex-bot-deployment.example.yaml) to create your own:

```shell
cp tex-bot-deployment.example.yaml tex-bot-deployment.yaml
```

By default, this file is read from the repository root.
Set the `TEX_BOT_CONFIG_PATH` [environment variable](https://wikipedia.org/wiki/Environment_variable) to keep it anywhere else.

> [!CAUTION]
> Your configuration file holds your [Discord bot token](https://itexus.com/glossary/discord-bot-token) and your SU platform [session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie).
> Anybody holding either can act as your bot, or read your group's members list.
> It is excluded by [`.gitignore`](.gitignore), so take care not to commit it or share it.

Only two settings must be filled in before TeX-Bot will start:

* `discord:bot-token`: The [Discord bot secret token](https://itexus.com/glossary/discord-bot-token) for the [instance of TeX-Bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts) you created.
  * This is available on [your bot's page in the Discord Developer Portal](https://discord.com/developers/applications).

* `discord:main-guild-id`: The [ID](https://discord.com/developers/docs/reference#snowflakes) of your community group's [Discord guild](https://discord.com/developers/docs/resources/guild).

Every other setting is optional, and its default is shown in [the example file](tex-bot-deployment.example.yaml) alongside an explanation of what it affects.
Some of the more commonly changed ones are:

* `logging:discord-channel:webhook-url`: The [webhook URL](https://support.discord.com/hc/articles/228383668-Intro-to-Webhooks) of the [Discord text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) where error log messages should be sent.
  * Error logs will **always** be sent to the [console](https://wikipedia.org/wiki/Terminal_emulator); this setting just allows them to also be sent to a [Discord log channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel).
  * Omit the whole `logging:discord-channel` section to disable this.

* `community-group:msl:organisation-id`: Your SU platform organisation ID, used to build your members list & other URLs.

* `community-group:msl:auth-cookie`: The SU platform [access session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie).
  * This [session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie) will [authenticate](https://wikipedia.org/wiki/Authentication) TeX-Bot to view your group's members list on the SU platform, as if it were [logged in to the website](https://wikipedia.org/wiki/Login_session) as a Committee member.
  * This can be [extracted from your web-browser](https://wikihow.com/View-Cookies), after logging in to view your members list yourself.
    It will most likely be listed as a [cookie](https://wikipedia.org/wiki/HTTP_cookie) named `.AspNet.SharedCookie`.
  * Leaving this unset disables SU platform access.
    Note that this will cause many commands & scheduled tasks to fail when they are used at runtime.

> [!NOTE]
> Settings are written in kebab-case & nested into sections.
> Throughout this documentation a setting is named by the path to it, separated by colons: `community-group:msl:auth-cookie` refers to `auth-cookie`, within `msl`, within `community-group`.
>
> Lengths of time are written largest-unit-first, in the format `<days>d<hours>h<minutes>m<seconds>s`, so `1h30m` & `2d` are both valid.
> Every part must carry its unit, so a bare `24` is rejected rather than being read as 24 seconds.

An invalid configuration file is never applied.
TeX-Bot reports the line responsible & keeps running on the last configuration that loaded successfully.

#### Changing Settings From Within Discord

Configuration can also be viewed & changed from within [Discord](https://discord.com), without editing the file by hand.
All of these [commands](https://discord.com/developers/docs/interactions/application-commands) require the "@**Committee**" [role](https://discord.com/developers/docs/topics/permissions#role-object), and reply only to the person that ran them:

* `/config get <setting>`: Shows what a setting is currently set to, & what it affects
* `/config set <setting> <value>`: Changes a single setting, then applies it
* `/config unset <setting>`: Returns a single setting to its default value
* `/config reload`: Reads the configuration file again, applying any changes made to it

Changing a setting rewrites your configuration file, keeping the comments & formatting you have added to it.

> [!IMPORTANT]
> If you edit the configuration file by hand, run `/config reload` before using `/config set` or `/config unset`.
> Both refuse to run against a file that has been edited since TeX-Bot last loaded it, so that a change made from within Discord is never quietly mixed together with one made by hand.

Most settings take effect as soon as they are applied, because they are read at the moment they are used.
A few are fixed while TeX-Bot is starting up & cannot be changed without restarting it; `/config reload` will tell you when one of those has changed.

#### Other [Environment Variables](https://wikipedia.org/wiki/Environment_variable)

Only two [environment variables](https://wikipedia.org/wiki/Environment_variable) are used, & both are optional:

* `TEX_BOT_CONFIG_PATH`: The location of your deployment configuration file.
  Defaults to `tex-bot-deployment.yaml` within the repository root
* `MESSAGES_FILE_PATH`: The location of [the messages file](messages.json), holding the welcome & roles messages TeX-Bot sends.
  Defaults to `messages.json` within the repository root

#### Migrating From an Older Version

Earlier versions of TeX-Bot were configured by [environment variables](https://wikipedia.org/wiki/Environment_variable), usually held in a `.env` file.
Those are no longer read at all, & a deployment still using them will start with only its default settings.

Move each value into your `tex-bot-deployment.yaml`, using the table below.
Where an old variable is not listed, [the example configuration file](tex-bot-deployment.example.yaml) names & explains every setting that exists.

| Old environment variable                     | Configuration setting                                    |
|----------------------------------------------|----------------------------------------------------------|
| `DISCORD_BOT_TOKEN`                          | `discord:bot-token`                                      |
| `DISCORD_GUILD_ID`                           | `discord:main-guild-id`                                  |
| `DISCORD_LOG_CHANNEL_WEBHOOK_URL`            | `logging:discord-channel:webhook-url`                    |
| `CONSOLE_LOG_LEVEL`                          | `logging:console:log-level`                              |
| `GROUP_NAME`                                 | `community-group:full-name`                              |
| `GROUP_SHORT_NAME`                           | `community-group:short-name`                             |
| `PURCHASE_MEMBERSHIP_URL`                    | `community-group:links:purchase-membership`              |
| `MEMBERSHIP_PERKS_URL`                       | `community-group:links:membership-perks`                 |
| `MODERATION_DOCUMENT_URL`                    | `community-group:links:moderation-policy`                |
| `CUSTOM_DISCORD_INVITE_URL`                  | `community-group:links:custom-discord-invite-link`       |
| `MEMBERSHIP_DEPENDENT_ROLES`                 | `community-group:membership-dependent-roles`             |
| `ORGANISATION_ID`                            | `community-group:msl:organisation-id`                    |
| `SU_PLATFORM_ACCESS_COOKIE`                  | `community-group:msl:auth-cookie`                        |
| `PING_COMMAND_EASTER_EGG_PROBABILITY`        | `commands:ping:easter-egg-probability`                   |
| `STATISTICS_DAYS`                            | `commands:stats:lookback-days`                            |
| `STATISTICS_ROLES`                           | `commands:stats:displayed-roles`                         |
| `MANUAL_MODERATION_WARNING_MESSAGE_LOCATION` | `commands:strike:performed-manually-warning-location`    |
| `SEND_INTRODUCTION_REMINDERS`                | `reminders:send-introduction-reminders:enabled`          |
| `SEND_INTRODUCTION_REMINDERS_DELAY`          | `reminders:send-introduction-reminders:delay`            |
| `SEND_INTRODUCTION_REMINDERS_INTERVAL`       | `reminders:send-introduction-reminders:interval`         |
| `SEND_GET_ROLES_REMINDERS`                   | `reminders:send-get-roles-reminders:enabled`             |
| `SEND_GET_ROLES_REMINDERS_DELAY`             | `reminders:send-get-roles-reminders:delay`               |
| `ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL` | `reminders:send-get-roles-reminders:interval`            |

Two differences are worth noting while migrating:

* Lengths of time are now written largest-unit-first (`1h30m`, not `30m1h`), & a delay is no longer required to be at least one day
* A comma-separated list, such as `STATISTICS_ROLES`, is now written as a [YAML list](https://yaml.org/spec/1.2.2/#collections)

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
