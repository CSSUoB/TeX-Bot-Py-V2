# Contributing

A big welcome and thank you for considering contributing to [CSS](https://cssbham.com)' [open-source](https://wikipedia.org/wiki/Open_source) projects!
We welcome anybody who wants to contribute, and we actively encourage everyone to do so, especially if you have never contributed before.

## Quick Links

* [Getting Started](#getting-started)
* [Using the Issue Tracker](#using-the-issue-tracker)
* [Repository Structure](#repository-structure)
* [Making Your First Contribution](#making-your-first-contribution)
* [License](#license)
* [Guidance](#guidance)

## Getting Started

If you have never used [Git](https://git-scm.com) before, we would recommend that you read [GitHub's Getting Started guide](https://guides.github.com/introduction/getting-started-with-git).
Additionally, linked below are some helpful resources:

* [GitHub git guides](https://github.com/git-guides)
* [git - the simple guide](https://rogerdudler.github.io/git-guide)
* [Getting Git Right (Atlassian)](https://atlassian.com/git)

If you are new to contributing to open-source projects on GitHub, the general workflow is as follows:

1. [Fork](https://w3schools.com/git/git_remote_fork.asp) this [repository](https://phoenixnap.com/kb/what-is-a-git-repository#ftoc-heading-1) and [clone](https://w3schools.com/git/git_clone.asp) it
2. Create a [branch](https://w3schools.com/git/git_remote_branch.asp) off main
3. Make your changes and [commit](https://w3schools.com/git/git_commit.asp) them
4. [Push](https://w3schools.com/git/git_push_to_remote.asp) your local [branch](https://w3schools.com/git/git_remote_branch.asp) to your remote fork
5. Open a new [pull request on GitHub](https://w3schools.com/git/git_remote_send_pull_request.asp)

We recommend also reading the following if you're unsure or not confident:

* [How To Make A Pull Request](https://makeapullrequest.com)
* [Contributing To An Open Source Project For The First Time](https://firsttimersonly.com)

TeX-Bot is written in [Python](https://python.org) using [Pycord](https://pycord.dev) and uses Discord's [slash-commands](https://support.discord.com/hc/articles/1500000368501-Slash-Commands-FAQ) & [user-commands](https://guide.pycord.dev/interactions/application-commands/context-menus).
We would recommend being somewhat familiar with the [Pycord library](https://docs.pycord.dev), [Python language](https://docs.python.org/3/reference/index) & [project terminology](README.md#terminology) before contributing.

## Using the Issue Tracker

We use [GitHub issues](https://docs.github.com/issues) to track bugs and feature requests.
If you find an issue with TeX-Bot, the best place to report it is through the issue tracker.
If you are looking for issues to contribute code to, it's a good idea to look at the [issues labelled "good-first-issue"](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues?q=label%3A%22good+first+issue%22)!

When submitting an issue, please be as descriptive as possible.
If you are submitting a bug report, please include the steps to reproduce the bug, and the environment it is in.
If you are submitting a feature request, please include the steps to implement the feature.

## Repository Structure

### Top level files

* [`main.py`](main.py): is the main entrypoint to instantiate the [`Bot` object](https://docs.pycord.dev/stable/api/clients.html#discord.Bot) & run it
* [`exceptions.py`](exceptions.py): contains common [exception](https://docs.python.org/3/tutorial/errors) subclasses that may be raised when certain errors occur
* [`config.py`](config.py): retrieves the [environment variables](README.md#setting-environment-variables) & populates the correct values into the `settings` object

### Other significant directories

* [`cogs/`](cogs): contains all the [cogs](https://guide.pycord.dev/popular-topics/cogs) within this project, see [below](#cogs) for more information
* [`utils/`](utils): contains common utility classes & functions used by the top-level modules & cogs
* [`db/core/models/`](db/core/models): contains all the [database ORM models](https://docs.djangoproject.com/en/stable/topics/db/models) to interact with storing information longer-term (between individual command events)
* [`tests/`](tests): contains the complete test suite for this project, based on the [Pytest framework](https://pytest.org)

### Cogs

[Cogs](https://guide.pycord.dev/popular-topics/cogs) are attachable modules that are loaded onto the [`Bot` instance](https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot).
They combine related [listeners](https://guide.pycord.dev/getting-started/more-features#event-handlers) and [commands](https://guide.pycord.dev/category/application-commands) (each as individual methods) into one class.
There are separate cog files for each activity, and one [`__init__.py`](cogs/__init__.py) file which instantiates them all:

<!--- pyml disable-next-line no-emphasis-as-heading -->
*For more information about the purpose of each cog, please look at the documentation within the files themselves*

* [`cogs/__init__.py`](cogs/__init__.py): instantiates all the cog classes within this directory

* [`cogs/archive.py`](cogs/archive.py): cogs for archiving categories of channels within your group's Discord guild

* [`cogs/command_error.py`](cogs/command_error.py): cogs for sending error messages when commands fail to complete/execute

* [`cogs/delete_all.py`](cogs/delete_all.py): cogs for deleting all permanent data stored in a specific object's table in the database

* [`cogs/edit_message.py`](cogs/edit_message.py): cogs for editing messages that were previously sent by TeX-Bot

* [`cogs/induct.py`](cogs/induct.py): cogs for inducting people into your group's Discord guild

* [`cogs/kill.py`](cogs/kill.py): cogs related to the shutdown of TeX-Bot

* [`cogs/make_member.py`](cogs/make_member.py): cogs related to making guests into members

* [`cogs/ping.py`](cogs/ping.py): cog to request a [ping](https://wikipedia.org/wiki/Ping-pong_scheme#Internet) response

* [`cogs/remind_me.py`](cogs/remind_me.py): cogs to ask TeX-Bot to send a reminder message at a later date

* [`cogs/send_get_roles_reminders.py`](cogs/send_get_roles_reminders.py): cogs relating to sending reminders, to Discord members, about opt-in roles.
(See [Repeated Tasks Conditions](README.md#repeated-tasks-conditions) for which conditions are required to be met, to execute this task)

* [`cogs/send_introduction_reminders.py`](cogs/send_introduction_reminders.py): cogs relating to sending reminders, to Discord members, about introducing themselves.
(See [Repeated Tasks Conditions](README.md#repeated-tasks-conditions) for which conditions are required to be met, to execute this task)

* [`cogs/source.py`](cogs/source.py): cogs for displaying information about the source-code of this project

* [`cogs/startup.py`](cogs/startup.py): cogs for startup & bot initialisation

* [`cogs/stats.py`](cogs/stats.py): cogs for displaying stats about your group's Discord guild, as well as its channels & Discord members

* [`cogs/strike.py`](cogs/strike.py): cogs for applying moderation actions to Discord members

* [`cogs/write_roles.py`](cogs/write_roles.py): cogs relating to sending the message that contains all the opt-in roles, into the "#**roles**" channel

## Making Your First Contribution

After you have found an issue which needs solving, it's time to start working on a fix!
However, there are a few guidelines we would like you to follow first.

### Installing pre-commit

[pre-commit](https://pre-commit.com) is a selection of checks and reformatting scripts that run before your changes are committed to git.
This ensures common formatting mistakes (see [the section on Code Style](#code-style)) and errors can be reported to you early, rather than having to wait for them to show in the CI/CD pipeline.
The hooks can be installed with the following command:

```shell
uv run pre-commit install --install-hooks
```

### Running tests

To ensure your changes adhere to the required functionality of this project, a test suite has been provided in [the `tests` directory](tests).
The test suite uses [Pytest](https://pytest.org), and can be run with the following command:

```shell
uv run pytest
```

Pycharm & VS Code also provide GUI interfaces to run the Pytest test suite.

### Code Style

In general, follow the formatting in the file you are editing.
You should also run the [static analysis linting](https://wikipedia.org/wiki/Lint_(software))/[type checking](https://realpython.com/python-type-checking#static-type-checking) tools to validate your code.

#### ruff

[Ruff](https://ruff.rs) is a [static analysis code linter](https://wikipedia.org/wiki/Lint_(software)), which will alert you to possible formatting mistakes in your Python code.
It can be run with the following command:

```shell
uv run ruff check
```

There are many additional flags to provide more advanced linting help (E.g. `--fix`).
See [ruff's documentation](https://docs.astral.sh/ruff/configuration#command-line-interface) for additional configuration options.

#### mypy

[Mypy](https://mypy-lang.org) is a [static type checker](https://realpython.com/python-type-checking#static-type-checking), which will alert you to possible [typing](https://realpython.com/python-type-checking#type-systems) errors in your Python code.
It can be run with the following command:

```shell
uv run mypy .
```

Although there is [a PyCharm plugin](https://github.com/leinardi/mypy-pycharm#mypy-pycharm) to provide GUI control & inline warnings for [mypy](https://mypy-lang.org), it has been rather temperamental recently.
So it is suggested to avoid using it, and run [mypy](https://mypy-lang.org) from the command-line instead.

#### PyMarkdown

[PyMarkdown](https://github.com/jackdewinter/pymarkdown) is a static analysis [Markdown](https://markdownguide.org/getting-started#what-is-markdown) [linter](https://wikipedia.org/wiki/Lint_(software)), which will alert you to possible formatting mistakes in your [MarkDown](https://markdownguide.org/getting-started#what-is-markdown) files.
It can be run with the following command:

```shell
uv run ccft-pymarkdown scan-all --with-git
```

This command includes the removal of custom-formatted tables. See the [CCFT-PyMarkdown tool](https://github.com/CarrotManMatt/CCFT-PyMarkdown) for more information on linting Markdown files that contain custom-formatted tables.

### Git Commit Messages

Commit messages should be written in the imperative present tense. For example, "Fix bug #1".

Commit subjects should start with a capital letter and **not** end in a full-stop.

Additionally, we request that you keep the commit subject under 80 characters for a comfortable viewing experience on GitHub and other git tools.
If you need more, please use the body of the commit.
(See [Robert Painsi's Commit Message Guidelines](https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53) for how to write good commit messages.)

For example:

```text
Fix TeX becoming sentient

<more detailed description here>
```

### What Happens Next?

Once you have made your changes, please describe them in your pull request in full.
We will then review them and communicate with you on GitHub.
We may ask you to change a few things, so please do check GitHub or your emails frequently.

After that, that's it! You've made your first contribution. 🎉

## License

Please note that any contributions you make will be made under the terms of the [Apache Licence 2.0](LICENSE).

## Guidance

We aim to get more people involved with our projects, and help build members' confidence in using git and contributing to open-source.
If you see an error, we encourage you to **be bold** and fix it yourself, rather than just raising an issue.
If you are stuck, need help, or have a question, the best place to ask is on our Discord.

Happy contributing!
