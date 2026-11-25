# Contributing

A big welcome and thank you for considering contributing to [CSS](https://cssbham.com)' [open-source](https://wikipedia.org/wiki/Open_source) projects!
We welcome anybody who wants to contribute, and we actively encourage everyone to do so, especially if you have never contributed before.

## Quick Links

* [Getting Started](#getting-started)
* [Using the Issue Tracker](#using-the-issue-tracker)
* [Repository Structure](#repository-structure)
* [Making Your First Contribution](#making-your-first-contribution)
* [Guides](#guides)
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
2. Create a [branch](https://w3schools.com/git/git_remote_branch.asp) from `main`
3. Make your changes and [commit](https://w3schools.com/git/git_commit.asp) them
4. [Push](https://w3schools.com/git/git_push_to_remote.asp) your local [branch](https://w3schools.com/git/git_remote_branch.asp) to your remote fork
5. Open a new [pull request on GitHub](https://w3schools.com/git/git_remote_send_pull_request.asp)

We recommend also reading the following if you're unsure or not confident:

* [How To Make A Pull Request](https://makeapullrequest.com)
* [Contributing To An Open Source Project For The First Time](https://firsttimersonly.com)

TeX-Bot is written in [Python](https://python.org) using [Pycord](https://pycord.dev) and uses Discord's [slash commands](TERMINOLOGY.md#slash-commands) & [user commands](TERMINOLOGY.md#user-commands).
We would recommend being somewhat familiar with the [Pycord library](https://docs.pycord.dev), [Python language](https://docs.python.org/3/reference/index) & [project terminology](TERMINOLOGY.md) before contributing.

## Using the Issue Tracker

We use [GitHub issues](https://docs.github.com/issues) to track bugs and feature requests.
If you find an issue with TeX-Bot, the best place to report it is through the issue tracker.
If you are looking for issues to contribute code to, it's a good idea to look at the [issues labelled "good-first-issue"](https://github.com/CSSUoB/TeX-Bot-Py-V2/issues?q=label%3A%22good+first+issue%22)!

When submitting an issue, please be as descriptive as possible.
If you are submitting a bug report, please include the steps to reproduce the bug and the environment it is in.
If you are submitting a feature request, please include the steps to implement the feature.

## Repository Structure

### Top level files

* [`main.py`](main.py): is the main entrypoint to instantiate the [`Bot` object](https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot) & run it
* [`config.py`](config.py): retrieves the [environment variables](DEPLOYMENT.md#setting-environment-variables) & populates the correct values into the `settings` object
* [`messages.json`](messages.json): contains the common messages sent by TeX-Bot (the welcome messages & the opt-in roles messages)
* [`TERMINOLOGY.md`](TERMINOLOGY.md): contains the definitions of the terms used throughout this project's documentation
* [`DEPLOYMENT.md`](DEPLOYMENT.md): contains the guide on how to deploy TeX-Bot, both in production & locally

### Other significant directories

* [`cogs/`](cogs): contains all the [cogs](https://guide.pycord.dev/popular-topics/cogs) within this project, see [below](#cogs) for more information
* [`exceptions/`](exceptions): contains common [exception](https://docs.python.org/3/tutorial/errors) subclasses that may be raised when certain errors occur
* [`utils/`](utils): contains common utility classes & functions used by the top-level modules & cogs
* [`db/core/models/`](db/core/models): contains all the [database ORM models](https://docs.djangoproject.com/en/stable/topics/db/models) to interact with storing information longer-term (between individual command events)
* [`tests/`](tests): contains the complete test suite for this project, based on the [Pytest framework](https://pytest.org)
* [`stubs/`](stubs): contains [type stubs](https://typing.python.org/en/latest/spec/distributing.html#stub-files) for third-party libraries that do not provide their own complete type hints

### Cogs

[Cogs](https://guide.pycord.dev/popular-topics/cogs) are attachable modules that are loaded onto the [`Bot` instance](https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot).
They combine related [listeners](https://guide.pycord.dev/getting-started/more-features#event-handlers) and [commands](https://guide.pycord.dev/category/application-commands) (each as individual methods) into one class.
There are separate cog files for each activity, and one [`__init__.py`](cogs/__init__.py) file which instantiates them all:

> [!IMPORTANT]
> For more information about the purpose of each cog, please look at the documentation within the files themselves

* [`cogs/__init__.py`](cogs/__init__.py): instantiates all the cog classes within this directory

* [`cogs/add_users_to_threads_and_channels.py`](cogs/add_users_to_threads_and_channels.py): cogs for adding users & roles to channels and threads, including automatically adding the committee roles to new committee threads

* [`cogs/annual_handover_and_reset.py`](cogs/annual_handover_and_reset.py): cogs for annual handover procedures and role resets

* [`cogs/archive.py`](cogs/archive.py): cogs for archiving categories of channels within your group's Discord guild

* [`cogs/check_su_platform_authorisation.py`](cogs/check_su_platform_authorisation.py): cogs for checking the current status of the supplied SU platform access cookie

* [`cogs/command_error.py`](cogs/command_error.py): cogs for sending error messages when commands fail to complete/execute

* [`cogs/committee_actions_tracking.py`](cogs/committee_actions_tracking.py): cogs for creating, assigning & tracking actions for committee members

* [`cogs/delete_all.py`](cogs/delete_all.py): cogs for deleting all permanent data stored in a specific object's table in the database

* [`cogs/edit_message.py`](cogs/edit_message.py): cogs for editing messages that were previously sent by TeX-Bot

* [`cogs/everest.py`](cogs/everest.py): cog to calculate how many steps of Mount Everest an assignment is worth

* [`cogs/induct.py`](cogs/induct.py): cogs for inducting people into your group's Discord guild

* [`cogs/invite_link.py`](cogs/invite_link.py): cog to display the invite link to your group's Discord guild

* [`cogs/kill.py`](cogs/kill.py): cogs related to the shutdown of TeX-Bot

* [`cogs/make_applicant.py`](cogs/make_applicant.py): cogs related to making users into applicants

* [`cogs/make_member.py`](cogs/make_member.py): cogs related to making guests into members

* [`cogs/ping.py`](cogs/ping.py): cog to request a [ping](https://wikipedia.org/wiki/Ping-pong_scheme#Internet) response

* [`cogs/send_get_roles_reminders.py`](cogs/send_get_roles_reminders.py): cogs relating to sending reminders, to Discord members, about opt-in roles.
(See [Repeated Tasks Conditions](README.md#repeated-tasks-conditions) for which conditions are required to be met to execute this task)

* [`cogs/send_introduction_reminders.py`](cogs/send_introduction_reminders.py): cogs relating to sending reminders, to Discord members, about introducing themselves.
(See [Repeated Tasks Conditions](README.md#repeated-tasks-conditions) for which conditions are required to be met to execute this task)

* [`cogs/source.py`](cogs/source.py): cogs for displaying information about the source-code of this project

* [`cogs/startup.py`](cogs/startup.py): cogs for startup & bot initialisation

* [`cogs/stats/`](cogs/stats): cogs for displaying stats about your group's Discord guild, as well as its channels & Discord members

* [`cogs/strike.py`](cogs/strike.py): cogs for applying moderation actions to Discord members

* [`cogs/write_roles.py`](cogs/write_roles.py): cogs relating to sending the message that contains all the opt-in roles, into the "#**roles**" channel

## Making Your First Contribution

After you have found an issue which needs solving, it's time to start working on a fix!
However, there are a few guidelines we would like you to follow first.

### Installing pre-commit Hooks

[pre-commit hooks](https://pre-commit.com) are a selection of checks and reformatting scripts that run before your changes are committed to git.
This ensures common formatting mistakes (see [the section on Code Style](#code-style)) and errors can be reported to you early, rather than having to wait for them to show in the CI/CD pipeline.
This project uses [prek](https://prek.j178.dev) to install & run the hooks, which is installed automatically along with this project's other development dependencies.
The hooks can be installed with the following command:

```shell
uv run prek install --prepare-hooks
```

The hooks will then run automatically on your changed files every time you make a commit.
To run all the hooks against every file in the repository, use the following command:

```shell
uv run prek run --all-files
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

[ruff](https://ruff.rs) is a [static analysis code linter](https://wikipedia.org/wiki/Lint_(software)), which will alert you to possible formatting mistakes in your Python code.
It can be run with the following command:

```shell
uv run ruff check
```

There are many additional flags to provide more advanced linting help (E.g. `--fix`).
See [ruff's documentation](https://docs.astral.sh/ruff/configuration#command-line-interface) for additional configuration options.

#### flake8

[flake8](https://flake8.pycqa.org) is another [static analysis code linter](https://wikipedia.org/wiki/Lint_(software)).
It is used alongside [ruff](#ruff) to check this project's own custom linting rules (provided by the [flake8-carrot](https://github.com/CarrotManMatt/flake8-carrot) plugin).
It can be run with the following command:

```shell
uv run flake8
```

#### mypy

[Mypy](https://mypy-lang.org) is a [static type checker](https://realpython.com/python-type-checking#static-type-checking), which will alert you to possible [typing](https://realpython.com/python-type-checking#type-systems) errors in your Python code.
It can be run with the following command:

```shell
uv run mypy .
```

#### PyMarkdown

[PyMarkdown](https://github.com/jackdewinter/pymarkdown) is a static analysis [Markdown](https://markdownguide.org/getting-started#what-is-markdown) [linter](https://wikipedia.org/wiki/Lint_(software)), which will alert you to possible formatting mistakes in your [MarkDown](https://markdownguide.org/getting-started#what-is-markdown) files.
It can be run with the following command:

```shell
uv run pymarkdown scan .
```

### Git Commit Messages

Commit messages should be written in the imperative present tense. For example, "Fix bug #1".

Commit subjects should start with a capital letter and **not** end in a full-stop.

Additionally, the commit subject must be 72 characters or fewer for a comfortable viewing experience on GitHub and other git tools.
If you need more, please use the body of the commit, keeping each line of the body to 80 characters or fewer.
(These rules are checked by [gitlint](https://jorisroovers.com/gitlint), which is installed as one of the [pre-commit hooks](#installing-pre-commit-hooks).)
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

## Guides

### Creating a New Cog

Cogs are modular components of TeX-Bot that group related [commands](TERMINOLOGY.md#application-commands) and [event listeners](TERMINOLOGY.md#event-listeners) into a single class.
To create a new cog, follow these steps:

1. Create the Cog File
   * Navigate to the `cogs/` directory.
   * Create a new Python file with a name that reflects the purpose of the cog (E.g. `example.py`).

2. Define the Cog Class
   * Define a class that inherits from `TeXBotBaseCog` (found within the `utils` module).
   * Name the class after the functionality it provides, ending in `Cog` (E.g. `PingCommandCog` or `SendIntroductionRemindersTaskCog`).
   * Add a docstring to describe the purpose of the cog.
   * Add the name of the cog class to the `__all__` sequence at the top of the file.

3. Add Commands and Event Listeners
   * Define a method within the class for each [command](TERMINOLOGY.md#application-commands) & [event listener](TERMINOLOGY.md#event-listeners).
   * Use the `@discord.slash_command()` decorator for [slash commands](TERMINOLOGY.md#slash-commands), the `@discord.user_command()` or `@discord.message_command()` decorators for [context commands](TERMINOLOGY.md#context-commands), or the `@TeXBotBaseCog.listener()` decorator for [event listeners](TERMINOLOGY.md#event-listeners).
   * Include any necessary checks using the `CommandChecks` decorators (found within the `utils` module).
     E.g. `@CommandChecks.check_interaction_user_in_main_guild` ensures that the user is a member of your group's main [Discord guild](TERMINOLOGY.md#guild-vs-server), and `@CommandChecks.check_interaction_user_has_committee_role` ensures that the user has the "@**Committee**" role.

   Example:

   ```python
   """Contains cog classes for any example interactions."""

   __all__: Sequence[str] = ("ExampleCommandCog",)

   import logging
   lazy from collections.abc import Sequence
   lazy from logging import Logger
   lazy from typing import Final

   import discord

   from utils import CommandChecks, TeXBotBaseCog
   lazy from utils import TeXBotApplicationContext

   logger: Final[Logger] = logging.getLogger("TeX-Bot")


   class ExampleCommandCog(TeXBotBaseCog):
       """Cog class that defines the "/example" command and its call-back method."""

       @discord.slash_command(name="example", description="Replies with an example message.")
       @CommandChecks.check_interaction_user_in_main_guild
       async def example(self, ctx: TeXBotApplicationContext) -> None:
           """Definition & callback response of the "example" command."""
           await ctx.respond(content="This is an example message.", ephemeral=True)

       @TeXBotBaseCog.listener()
       async def on_member_join(self, member: discord.Member) -> None:
           """Log the name of every new member that joins your group's Discord guild."""
           logger.debug("%s joined your group's Discord guild.", member)
   ```

4. Register the Cog
   * Edit `cogs/__init__.py` to import your new cog class, and add it to the list of cogs in the `setup` function.
   * Also, include the cog class in the `__all__` sequence to ensure it is properly exported.
   * Keep the `__all__` sequence & the imports in alphabetical order.

   Example:

   ```python
   __all__: Sequence[str] = (
       ...,
       "EverestCommandCog",
       "ExampleCommandCog",
       ...,
   )

   # ...
   from .everest import EverestCommandCog
   from .example import ExampleCommandCog
   # ...


   def setup(bot: TeXBot) -> None:
       """Add all the cogs to the bot, at bot startup."""
       cogs: Iterable[type[TeXBotBaseCog]] = (
           ...,
           EverestCommandCog,
           ExampleCommandCog,
           ...,
       )
       Cog: type[TeXBotBaseCog]
       for Cog in cogs:
           bot.add_cog(Cog(bot))
   ```

5. Test the Cog
   * Run the bot with your changes and ensure the new cog is loaded without errors.
   * Test the [commands](TERMINOLOGY.md#application-commands) and [event listeners](TERMINOLOGY.md#event-listeners) to verify they work as expected.

6. Document the Cog
   * Every class & method requires a docstring (this is checked by [ruff](#ruff)).
     Only add extra comments where the functionality may be unexpected or surprising.
   * Add your new cog file to [the list of cogs](#cogs) within this document.
   * If your cog adds any new functionality, add it to [the "Features" section](README.md#features) of the `README.md` file.

### Creating a New Environment Variable

To add a new [environment variable](https://wikipedia.org/wiki/Environment_variable) to the project, follow these steps:

1. Define the Variable in your development `.env` file
   * Open the `.env` file in the project root directory (or create one if it doesn't exist).
   * Add the new variable in the format `VARIABLE_NAME=value`.
   * Ensure the variable name is descriptive and uses uppercase letters with underscores.

2. Update `config.py`
   * Open the `config.py` file.
   * Add a new private setup class method in the `Settings` class (named `_setup_<variable_name>`) to validate and load the variable.
   * Raise an `ImproperlyConfiguredError` with a helpful message if the value of the variable is invalid.
   * Store the final value in `cls._settings` under the variable's key (this is usually the same as the variable's name).
   * Every key that is retrieved from `settings` must be present in `cls._settings` once setup has completed, in every circumstance.
     So, if an optional variable has not been set, either store its default value or `None` as the value.
     (The only exceptions are variables that just configure logging & are never retrieved from `settings`, such as `DISCORD_LOG_LEVEL`.)

   Example:

   ```python
   @classmethod
   def _setup_example_limit(cls) -> None:
       raw_example_limit: str = os.getenv("EXAMPLE_LIMIT", default="3").strip()

       if not re.fullmatch(pattern=r"\A\d{1,3}\Z", string=raw_example_limit):
           INVALID_EXAMPLE_LIMIT_MESSAGE: Final[str] = (
               "EXAMPLE_LIMIT must be an integer between 0 and 999."
           )
           raise ImproperlyConfiguredError(INVALID_EXAMPLE_LIMIT_MESSAGE)

       cls._settings["EXAMPLE_LIMIT"] = int(raw_example_limit)
   ```

   * If the variable is required, raise an `ImproperlyConfiguredError` when it has not been set (see `_setup_discord_guild_id` for an example).
   * If the variable is optional & has no default value, store `None` when it has not been set (see `_setup_group_full_name` for an example).

3. Call the Setup Method
   * Add a call to your new setup method within the `try` block of the `_setup_env_variables` method in `config.py`.
   * If your setup method depends upon the value of another variable, it must be called after that variable's setup method.
     (E.g. `_setup_auto_su_platform_access_cookie_checking_interval` must be called after `_setup_auto_su_platform_access_cookie_checking`.)

   Example:

   ```python
   @classmethod
   def _setup_env_variables(cls) -> None:
       ...

       try:
           cls._setup_console_logging()
           ...
           cls._setup_auto_add_committee_to_threads()
           cls._setup_example_limit()
       except ImproperlyConfiguredError as improper_config_error:
           webhook_config_logger.error(improper_config_error.message)  # noqa: TRY400
           raise improper_config_error from improper_config_error

       cls._is_env_variables_setup = True
   ```

4. Use the Variable
   * Import the `settings` object from `config.py`, then retrieve the value of your variable using its key.

   Example:

   ```python
   lazy from config import settings

   example_limit: int = settings["EXAMPLE_LIMIT"]
   ```

5. Document the Variable
   * Add the variable to `.env.example`, along with comments describing its purpose & any valid values.
     The example value should be the variable's default value (if it has one).
   * If the variable is required, mark it with `# !!REQUIRED!!` in `.env.example`, and add it to the list of required variables in [the "Setting Environment Variables" section](DEPLOYMENT.md#setting-environment-variables) of `DEPLOYMENT.md`.

6. Test the Variable
   * Run the bot with your changes and ensure the new variable is loaded correctly.
   * Test edge cases, such as missing, blank or invalid values in the `.env` file, to confirm that error handling functions correctly.

### Creating a Response Button

Response buttons are interactive [message components](TERMINOLOGY.md#interactions) that allow users to respond to bot messages with predefined actions.
To create a response button, follow these steps:

1. Define the View Class
   * Create a new class in your cog file that inherits from `discord.ui.View`.
   * Add a button callback response method for each button, using the `@discord.ui.button()` decorator.
   * Each button should define its label, style and a unique custom ID.

   Example:

   ```python
   import discord
   from discord.ui import View


   class ConfirmActionView(View):
       """A discord.View containing two buttons to confirm or cancel an action."""

       @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="confirm_yes")
       async def confirm_yes_button_callback(
           self, _: discord.ui.Button[ConfirmActionView], interaction: discord.Interaction
       ) -> None:
           """When the "Yes" button is pressed, confirm the action."""
           await interaction.response.send_message(content="Action confirmed.", ephemeral=True)

       @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="confirm_no")
       async def confirm_no_button_callback(
           self, _: discord.ui.Button[ConfirmActionView], interaction: discord.Interaction
       ) -> None:
           """When the "No" button is pressed, cancel the action."""
           await interaction.response.send_message(content="Action cancelled.", ephemeral=True)
   ```

2. Send the View with a Message
   * Use the `view` parameter of the `send` or `respond` method to attach the buttons to a message.
   * This could be sent in response to a [command](TERMINOLOGY.md#application-commands), [event](TERMINOLOGY.md#events) or [task](TERMINOLOGY.md#tasks).

   Example:

   ```python
   await ctx.respond(content="Do you want to proceed?", view=ConfirmActionView())
   ```

3. Handle Button Interactions
   * Define the logic within each button callback method to handle the user's [interaction](TERMINOLOGY.md#interactions).
   * Use `interaction.response` to send feedback or perform actions based on the button that was pressed.
   * The `button` argument of the callback method can be used to retrieve information about the button that was pressed.

   Example:

   ```python
   @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="confirm_yes")
   async def confirm_yes_button_callback(
       self, button: discord.ui.Button[ConfirmActionView], interaction: discord.Interaction
   ) -> None:
       """When the "Yes" button is pressed, tell the user which button they pressed."""
       if interaction.user is None:
           await interaction.response.send_message(
               content="No user information was provided.", ephemeral=True
           )
           return

       await interaction.response.send_message(
           content=f"{interaction.user.mention} pressed the {button.label!r} button.",
           ephemeral=True,
       )
   ```

   Alternatively, the button callback methods can be kept lightweight, with processing continuing inside the original cog method that sent the buttons.
   In this case, each button callback method only removes the buttons from the message, while the original cog method waits for the button [interaction](TERMINOLOGY.md#interactions) using `self.bot.wait_for()`.
   The value of `button_interaction.data["custom_id"]` can then be checked to decide how to continue.

   Example button callback method:

   ```python
   @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="confirm_yes")
   async def confirm_yes_button_callback(
       self, _: discord.ui.Button[ConfirmActionView], interaction: discord.Interaction
   ) -> None:
       """
       Remove the buttons from the message when the "Yes" button is pressed.

       The actual handling of the event is done by the command that sent the view,
       so all that is required is to remove the buttons from the original message.
       """
       await interaction.response.edit_message(view=None)
   ```

   Example of waiting for the button interaction within the original cog method:

   ```python
   button_interaction: discord.Interaction = await self.bot.wait_for(
       "interaction",
       check=lambda interaction: (
           interaction.type == discord.InteractionType.component
           and interaction.user == ctx.user
           and interaction.channel == ctx.channel
           and "custom_id" in interaction.data
           and interaction.data["custom_id"] in {"confirm_yes", "confirm_no"}
       ),
   )

   if button_interaction.data["custom_id"] == "confirm_no":  # type: ignore[index, typeddict-item]
       await button_interaction.edit_original_response(content="Action cancelled.", view=None)
       return
   ```

   See the `/strike` [command](TERMINOLOGY.md#application-commands) for a full example ([command handler](https://github.com/CSSUoB/TeX-Bot-Py-V2/blob/9376f67561cbdd7016fba7ea0c84372e1782f0e6/cogs/strike.py#L110-L145), [follow-up handling](https://github.com/CSSUoB/TeX-Bot-Py-V2/blob/9376f67561cbdd7016fba7ea0c84372e1782f0e6/cogs/strike.py#L296-L323)).

4. Test the Button
   * Run the bot with your changes and ensure the buttons appear and function as expected.
   * Test edge cases, such as multiple users interacting with the buttons simultaneously.

5. Document the Button
   * Every class & method requires a docstring (this is checked by [ruff](#ruff)).
     Only add extra comments where the functionality may be unexpected or surprising.

### Creating and Interacting with Django Models

> [!IMPORTANT]
> When making changes to the database models, it is essential to consider the data protection implications of these changes.
> If personal data is being collected, stored or processed, it is essential that this is in compliance with the law.
> In the UK, the relevant law is the [Data Protection Act 2018](https://www.legislation.gov.uk/ukpga/2018/12/contents).
> As a general rule, any changes that have data protection implications should be checked and approved by the organisation responsible for running the application.

[Django models](https://docs.djangoproject.com/en/stable/topics/db/models) are used to interact with the database in this project.
They allow you to define the structure of your data and provide an API to query and manipulate it.
To create and interact with Django models, follow these steps:

1. Define a Model
   * Open the `db/core/models/__init__.py` file, which contains all of TeX-Bot's models.
   * Define a new class that inherits from `AsyncBaseModel` (found within the `.utils` module in `db/core/models/`).
   * Add the name of the class to the `__all__` sequence at the top of the file (keeping it in alphabetical order).
   * Add your Django fields to the class to represent the model's data structure.
   * If your model stores information related to each [Discord member](TERMINOLOGY.md#discord-objects), you **must** declare a field called `discord_member`, which links to the `DiscordMember` model (also found within the `.utils` module in `db/core/models/`).
     The field must be either a Django `ForeignKey` field or a `OneToOneField`, depending upon the relationship between your model and each Discord member.
   * Define the static class string holding the display name for multiple instances of your class (E.g. `INSTANCES_NAME_PLURAL: str = "Discord Members' Smiley Faces"`).
   * Define a `Meta` class holding the human-readable names of your model.

   Example:

   ```python
   class MemberSmileyFaces(AsyncBaseModel):
       """Model to represent the number of smiley faces of each Discord member."""

       INSTANCES_NAME_PLURAL: str = "Discord Members' Smiley Faces"

       discord_member = models.OneToOneField(
           DiscordMember,
           on_delete=models.CASCADE,
           related_name="smiley_faces",
           verbose_name="Discord Member",
           blank=False,
           null=False,
           primary_key=True,
       )
       count = models.PositiveIntegerField(
           "Number of smiley faces",
           null=False,
           blank=True,
           default=0,
       )

       class Meta(TypedModelMeta):  # noqa: D106
           verbose_name: ClassVar[StrOrPromise] = _("Discord Member's Smiley Faces")
           verbose_name_plural: ClassVar[StrOrPromise] = _("Discord Members' Smiley Faces")
   ```

2. Create Migrations
   * Run the following command to create a migration file for your changes to the models:

   ```shell
   uv run python -m django makemigrations --settings=db._settings
   ```

   * Commit the new migration file (found within `db/core/migrations/`) along with the rest of your changes.
     Existing migration files must not be deleted.
   * You do not need to apply the migrations yourself, because any pending migrations are applied automatically every time TeX-Bot starts up.

3. Query the Model
   * Use Django's [asynchronous ORM methods](https://docs.djangoproject.com/en/stable/topics/async#queries-the-orm) (E.g. `acreate()`, `aget_or_create()`, `afirst()`, `asave()` & `adelete()`), because all of TeX-Bot's [commands](TERMINOLOGY.md#application-commands), [event listeners](TERMINOLOGY.md#event-listeners) & [tasks](TERMINOLOGY.md#tasks) are asynchronous.
   * Models related to each Discord member can be filtered using the Discord member's ID (E.g. `MemberSmileyFaces.objects.filter(discord_member__discord_id=member.id)`).
   * It is unlikely that you will need to query the `DiscordMember` model directly, other than to retrieve (or create) the `DiscordMember` object to link to a new instance of your model.
     Instead, the attributes of each Discord member can be accessed through the relationship between your model and the `DiscordMember` model.
   * The example below shows a single [slash command](TERMINOLOGY.md#slash-commands) that creates, filters, updates & deletes instances of a model, based upon the given command option.

   ```python
   """Contains cog classes for any smiley faces interactions."""

   __all__: Sequence[str] = ("SmileyFacesCommandCog",)

   lazy from collections.abc import Sequence

   import discord

   from utils import CommandChecks, TeXBotBaseCog
   lazy from db.core.models import DiscordMember, MemberSmileyFaces
   lazy from utils import TeXBotApplicationContext


   class SmileyFacesCommandCog(TeXBotBaseCog):
       """Cog class that defines the "/smiley-faces" command and its call-back method."""

       @discord.slash_command(
           name="smiley-faces", description="Add, view or reset your number of smiley faces."
       )
       @discord.option(
           name="action",
           description="The action to perform on your smiley faces.",
           input_type=str,
           choices={"add", "view", "reset"},
           required=True,
           parameter_name="action",
       )
       @CommandChecks.check_interaction_user_in_main_guild
       async def smiley_faces(self, ctx: TeXBotApplicationContext, action: str) -> None:
           """
           Definition & callback response of the "smiley_faces" command.

           The "smiley_faces" command creates, retrieves, updates or deletes
           the MemberSmileyFaces object of the user that ran the command.
           """
           if action == "add":
               member_smiley_faces: MemberSmileyFaces = (
                   await MemberSmileyFaces.objects.aget_or_create(
                       discord_member=(
                           await DiscordMember.objects.aget_or_create(discord_id=ctx.user.id)
                       )[0]
                   )
               )[0]
               member_smiley_faces.count += 1
               await member_smiley_faces.asave()

               await ctx.respond(
                   content=f"You now have {member_smiley_faces.count} smiley faces!",
                   ephemeral=True,
               )
               return

           found_smiley_faces: MemberSmileyFaces | None = await MemberSmileyFaces.objects.filter(
               discord_member__discord_id=ctx.user.id
           ).afirst()

           if found_smiley_faces is None:
               await ctx.respond(content="You do not have any smiley faces yet.", ephemeral=True)
               return

           if action == "view":
               await ctx.respond(
                   content=f"You have {found_smiley_faces.count} smiley faces.",
                   ephemeral=True,
               )
               return

           await found_smiley_faces.adelete()
           await ctx.respond(content="Your smiley faces have been reset.", ephemeral=True)
   ```

   * If the data stored by your model may need to be completely deleted in the future, add a matching sub-command to the `/delete-all` [command](TERMINOLOGY.md#application-commands) group within `cogs/delete_all.py`.

## License

Please note that any contributions you make will be made under the terms of the [Apache Licence 2.0](LICENSE).

## Guidance

We aim to get more people involved with our projects and help build members' confidence in using git and contributing to open-source.
If you see an error, we encourage you to **be bold** and fix it yourself, rather than just raising an issue.
If you are stuck, need help, or have a question, the best place to ask is on our Discord.

Happy contributing!
