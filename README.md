# TeX-Bot-Py-V2

[![Python Version](https://img.shields.io/badge/Python-3.15-blue?&logo=Python&logoColor=white)](https://python.org/downloads/release/python-3150)
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

> [!NOTE]
> Please familiarise yourself with all the terms defined in [TERMINOLOGY.md](TERMINOLOGY.md) before continuing, to prevent any confusion.

## Features

TeX-Bot provides the following functionality within your community group's [Discord guild](TERMINOLOGY.md#guild-vs-server):

* **Induction** - Give new [guests](TERMINOLOGY.md#community-group-membership) the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object) & welcome them into your [Discord guild](TERMINOLOGY.md#guild-vs-server).
(Using the `/induct` [slash command](TERMINOLOGY.md#slash-commands), the "Induct User" & "Silently Induct User" [user commands](TERMINOLOGY.md#user-commands) or the "Induct Message Author" [message command](TERMINOLOGY.md#message-commands).)
The `/ensure-members-inducted` [slash command](TERMINOLOGY.md#slash-commands) gives the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object) to any [members](TERMINOLOGY.md#community-group-membership) that are missing it.

* **Membership** - Allow [Discord members](TERMINOLOGY.md#discord-objects) to give themselves the "@**Member**" [role](https://discord.com/developers/docs/topics/permissions#role-object), after their membership ID has been validated against your group's members list on the SU platform (using the `/make-member` [slash command](TERMINOLOGY.md#slash-commands)).
The `/member-count` [slash command](TERMINOLOGY.md#slash-commands) displays how many [members](TERMINOLOGY.md#community-group-membership) your community group has.

* **Applicants** - Give [Discord members](TERMINOLOGY.md#discord-objects) the "@**Applicant**" [role](https://discord.com/developers/docs/topics/permissions#role-object).
(Using the `/make-applicant` [slash command](TERMINOLOGY.md#slash-commands), the "Make Applicant" [user command](TERMINOLOGY.md#user-commands) or the "Make Message Author Applicant" [message command](TERMINOLOGY.md#message-commands).)

* **Moderation** - Apply strikes to [Discord members](TERMINOLOGY.md#discord-objects), with the matching moderation action being performed automatically.
(Using the `/strike`, `/get-strikes` & `/decrement-strikes` [slash commands](TERMINOLOGY.md#slash-commands), the "Strike User" [user command](TERMINOLOGY.md#user-commands) or the "Strike Message Author" [message command](TERMINOLOGY.md#message-commands).)
Moderation actions that are applied manually (instead of by using the `/strike` [command](TERMINOLOGY.md#application-commands)) are also tracked.
The "Send Message to Committee" [message command](TERMINOLOGY.md#message-commands) forwards a message to your committee for discussion.

* **Committee Actions Tracking** - Create, assign, update & list actions for your committee members (using the `/committee-actions` group of [slash commands](TERMINOLOGY.md#slash-commands) or the "Action Message Author" [message command](TERMINOLOGY.md#message-commands)).

* **Reminders** - Send [Discord members](TERMINOLOGY.md#discord-objects) [repeated reminders](#repeated-tasks-conditions) to introduce themselves, and to give themselves opt-in [roles](https://discord.com/developers/docs/topics/permissions#role-object).

* **Annual Handover** - Give the "@**Committee**" [role](https://discord.com/developers/docs/topics/permissions#role-object) to the new committee (any [Discord members](TERMINOLOGY.md#discord-objects) with the "@**Committee-Elect**" [role](https://discord.com/developers/docs/topics/permissions#role-object)), reset the "@**Member**" & academic year [roles](https://discord.com/developers/docs/topics/permissions#role-object) and increment the academic year channels (using the `/committee-handover`, `/annual-roles-reset` & `/increment-year-channels` [slash commands](TERMINOLOGY.md#slash-commands)).

* **Channel Management** - Archive channels & categories (using the `/archive-channel` & `/archive-category` [slash commands](TERMINOLOGY.md#slash-commands)), and add [users](TERMINOLOGY.md#discord-objects) or [roles](https://discord.com/developers/docs/topics/permissions#role-object) to channels & threads (using the `/add-users-to-channel` & `/add-role-to-channel` [slash commands](TERMINOLOGY.md#slash-commands)).
The committee [roles](https://discord.com/developers/docs/topics/permissions#role-object) can also be automatically added to any new threads created within committee categories.

* **Statistics** - Display graphs of message statistics for a channel, your whole [Discord guild](TERMINOLOGY.md#guild-vs-server) or yourself, and of the [roles](https://discord.com/developers/docs/topics/permissions#role-object) that [Discord members](TERMINOLOGY.md#discord-objects) had when they left (using the `/stats` group of [slash commands](TERMINOLOGY.md#slash-commands)).

* **Bot Messages** - Send the opt-in [roles](https://discord.com/developers/docs/topics/permissions#role-object) message into the "#**roles**" channel (using the `/write-roles` [slash command](TERMINOLOGY.md#slash-commands)) and edit messages previously sent by TeX-Bot (using the `/edit-message` [slash command](TERMINOLOGY.md#slash-commands)).

* **SU Platform Authorisation Checking** - Check whether your `SU_PLATFORM_ACCESS_COOKIE` is valid, and which organisations it has administrative access to (using the `/check-su-platform-authorisation` [slash command](TERMINOLOGY.md#slash-commands)).
This check can also be run automatically as a [repeated task](#repeated-tasks-conditions).

* **Data Management** - Delete all of a specific type of data stored in the database (using the `/delete-all` group of [slash commands](TERMINOLOGY.md#slash-commands)).

* **Utilities** - `/ping`, `/source`, `/invite-link`, `/everest` & `/kill` (to shut down TeX-Bot).

## Error Codes

Members of your [Discord guild](https://discord.com/developers/docs/resources/guild) using TeX-Bot may encounter an error code when executing a slash-command fails.
If a user encounters any of these errors, please communicate the error to the committee member that has been assigned to upkeep & deployment of your instance of TeX-Bot.
The meaning of each error code is given here:

* `E1011` - The value for the [environment variable](https://wikipedia.org/wiki/Environment_variable) `DISCORD_GUILD_ID` is an [ID](https://discord.com/developers/docs/reference#snowflakes) that references a [Discord guild](TERMINOLOGY.md#guild-vs-server) that does not exist

* `E1021` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Committee**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/add-role-to-channel`, `/add-users-to-channel`, `/annual-roles-reset`, `/archive-category`, `/archive-channel`, `/check-su-platform-authorisation`, `/committee-handover`, `/decrement-strikes`, `/edit-message`, `/ensure-members-inducted`, `/get-strikes`, `/increment-year-channels`, `/induct`, `/kill`, `/make-applicant`, `/strike` & `/write-roles` [commands](TERMINOLOGY.md#application-commands).
It is also required for all the `/delete-all` [commands](TERMINOLOGY.md#application-commands), the `/committee-actions create`, `/committee-actions list`, `/committee-actions list-all`, `/committee-actions reassign`, `/committee-actions action-random-user` & `/committee-actions action-all-committee` [commands](TERMINOLOGY.md#application-commands), and the "Induct User", "Silently Induct User", "Induct Message Author", "Make Applicant", "Make Message Author Applicant", "Strike User", "Strike Message Author" & "Action Message Author" [context commands](TERMINOLOGY.md#context-commands).
The `/committee-actions list` [command](TERMINOLOGY.md#application-commands) only requires this [role](https://discord.com/developers/docs/topics/permissions#role-object) when listing the actions of another user.)

* `E1022` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Guest**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/induct`, `/ensure-members-inducted`, `/increment-year-channels`, `/make-applicant`, `/stats server` & `/stats self` [commands](TERMINOLOGY.md#application-commands), and the "Induct User", "Silently Induct User", "Induct Message Author", "Make Applicant" & "Make Message Author Applicant" [context commands](TERMINOLOGY.md#context-commands))

* `E1023` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Member**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/make-member`, `/ensure-members-inducted` & `/annual-roles-reset` [commands](TERMINOLOGY.md#application-commands))

* `E1024` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Archivist**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/archive-category` & `/increment-year-channels` [commands](TERMINOLOGY.md#application-commands))

* `E1025` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Applicant**". (This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/make-applicant` [command](TERMINOLOGY.md#application-commands) and respective user and message commands)

* `E1026` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [role](https://discord.com/developers/docs/topics/permissions#role-object) with the name "@**Committee-Elect**".
(This [role](https://discord.com/developers/docs/topics/permissions#role-object) is required for the `/committee-handover` [command](TERMINOLOGY.md#application-commands))

* `E1031` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) with the name "#**roles**".
(This [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) is required for the `/write-roles` [command](TERMINOLOGY.md#application-commands))

* `E1032` - Your [Discord guild](https://discord.com/developers/docs/resources/guild) does not contain a [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) with the name "#**general**".
(This [text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) is required for the `/induct` [command](TERMINOLOGY.md#application-commands) (unless the `silent` option is used), and the "Induct User" & "Induct Message Author" [context commands](TERMINOLOGY.md#context-commands))

* `E1042` - The reference to the `@everyone` [role](https://discord.com/developers/docs/topics/permissions#role-object) could not be correctly retrieved.
Try running the command that caused this error again.
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

The [configuration variables](https://wikipedia.org/wiki/Environment_variable) `SEND_INTRODUCTION_REMINDERS`, `SEND_GET_ROLES_REMINDERS` & `AUTO_SU_PLATFORM_ACCESS_COOKIE_CHECKING` determine whether their related [tasks](TERMINOLOGY.md#tasks) should run.
However, because the reminder [tasks](TERMINOLOGY.md#tasks) are rather annoying/drastic actions to be executed automatically, there are additional conditions that must be met on a per-[member](https://discord.com/developers/docs/resources/guild#guild-member-object) basis for the action to trigger.
The conditions for each [task](https://docs.pycord.dev/en/stable/ext/tasks) are listed below, along with the additional [environment variables](https://wikipedia.org/wiki/Environment_variable) that can be used to configure the conditions to suit your needs.

| Task Name               | Enable/Disable                                                                                                                                                                                                                                                                | Per-Member Conditions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Scheduled Interval                                                                                                                                                                                                                                                                                                                                                                  |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `send_introduction_reminders` | `SEND_INTRODUCTION_REMINDERS`:<br/>* `Once` - Only send the introduction reminder once (even if they later delete the message)<br/>* `Interval` - Send an introduction reminder at a set interval<br/>* `False` - Do not send introduction reminders                          | * The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not been inducted (does not have the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object))<br/>* The time since the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) joined your community's guild is greater than `SEND_INTRODUCTION_REMINDERS_DELAY`<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not opted out of introduction reminders<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not yet been sent an introduction reminder. (Only applies when `SEND_INTRODUCTION_REMINDERS` is set to the value `Once`)                                                                                   | The interval of time between this task running is determined by `SEND_INTRODUCTION_REMINDERS_INTERVAL`. (When `SEND_INTRODUCTION_REMINDERS` is set to the value `Once`, all [Discord members](https://discord.com/developers/docs/resources/guild#guild-member-object) will still be checked at this interval, just not sent a message if they have already been sent an introduction reminder). The default interval is to send messages every 6 hours |
| `send_get_roles_reminders` | `SEND_GET_ROLES_REMINDERS`:<br/>* `True` - A single reminder for the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) will be sent to them only once (even if they later delete the message)<br/>* `False` - Do not send any reminders for [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) | * The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has been inducted (has the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object))<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) does not have any of the opt-in [roles](https://discord.com/developers/docs/topics/permissions#role-object). (E.g. "@**First Year**" or "@**Anime**".) (Having the green "@**Member**" [role](https://discord.com/developers/docs/topics/permissions#role-object) or even the "@**Committee**" [role](https://discord.com/developers/docs/topics/permissions#role-object) makes no difference)<br/>* The time since the [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) was inducted (gained the "@**Guest**" [role](https://discord.com/developers/docs/topics/permissions#role-object)) is greater than `SEND_GET_ROLES_REMINDERS_DELAY`<br/>* The [Discord member](https://discord.com/developers/docs/resources/guild#guild-member-object) has not yet been sent a reminder to get [roles](https://discord.com/developers/docs/topics/permissions#role-object) | The interval of time between this task running is determined by `ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL`. It is unlikely that this value will need to be changed from the default of 24 hours                                                                                                                                                                                   |
| `su_platform_access_cookie_check_task` | `AUTO_SU_PLATFORM_ACCESS_COOKIE_CHECKING`:<br/>* `True` - Regularly check whether the `SU_PLATFORM_ACCESS_COOKIE` is still valid & log the result<br/>* `False` - Do not automatically check the `SU_PLATFORM_ACCESS_COOKIE` (this is the default) | None (this [task](TERMINOLOGY.md#tasks) does not send any messages to [Discord members](https://discord.com/developers/docs/resources/guild#guild-member-object)) | The interval of time between this task running is determined by `AUTO_SU_PLATFORM_ACCESS_COOKIE_CHECKING_INTERVAL`. The default interval is 24 hours |

## Deployment

The full guide on how to deploy TeX-Bot can be found in [DEPLOYMENT.md](DEPLOYMENT.md).
This includes [deploying TeX-Bot in production](DEPLOYMENT.md#deploying-in-production) using our pre-built [docker container](https://docker.com/resources/what-container), as well as [deploying TeX-Bot locally](DEPLOYMENT.md#local-deployment) for development & testing.

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

When selecting a version tag to use for [deploying TeX-Bot as a container image](DEPLOYMENT.md#deploying-in-production), there are multiple tag schemes available:

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
