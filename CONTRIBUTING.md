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
We would recommend being somewhat familiar with the [Pycord library](https://docs.pycord.dev), [Python language](https://docs.python.org/3/reference/index) & [project terminology](TERMINOLOGY.md) before contributing.

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
* [`exceptions/`](exceptions): contains common [exception](https://docs.python.org/3/tutorial/errors) subclasses that may be raised when certain errors occur
* [`config.py`](config.py): retrieves the [environment variables](README.md#setting-environment-variables) and populates the correct values into the `settings` object

### Other significant directories

* [`cogs/`](cogs): contains all the [cogs](https://guide.pycord.dev/popular-topics/cogs) within this project, see [below](#cogs) for more information
* [`utils/`](utils): contains common utility classes and functions used by the top-level modules and cogs
* [`db/core/models/`](db/core/models): contains all the [database ORM models](https://docs.djangoproject.com/en/stable/topics/db/models) to interact with storing information longer-term (between individual command events)
* [`tests/`](tests): contains the complete test suite for this project, based on the [Pytest framework](https://pytest.org)

### Cogs

[Cogs](https://guide.pycord.dev/popular-topics/cogs) are attachable modules that are loaded onto the [`Bot` instance](https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot).
They combine related [listeners](https://guide.pycord.dev/getting-started/more-features#event-handlers) and [commands](https://guide.pycord.dev/category/application-commands) (each as individual methods) into one class.
There are separate cog files for each activity, and one [`__init__.py`](cogs/__init__.py) file which instantiates them all:

<!--- pyml disable-next-line no-emphasis-as-heading-->
*For more information about the purpose of each cog, please look at the documentation within the files themselves*

* [`cogs/__init__.py`](cogs/__init__.py): instantiates all the cog classes within this directory

* [`cogs/annual_handover_and_reset.py`](cogs/annual_handover_and_reset.py): cogs for annual handover procedures and role resets

* [`cogs/archive.py`](cogs/archive.py): cogs for archiving categories of channels within your group's Discord guild

* [`cogs/command_error.py`](cogs/command_error.py): cogs for sending error messages when commands fail to complete/execute

* [`cogs/delete_all.py`](cogs/delete_all.py): cogs for deleting all permanent data stored in a specific object's table in the database

* [`cogs/edit_message.py`](cogs/edit_message.py): cogs for editing messages that were previously sent by TeX-Bot

* [`cogs/get_token_authorisation.py`](cogs/get_token_authorisation.py): cogs for retrieving the current status of the supplied authentication token

* [`cogs/induct.py`](cogs/induct.py): cogs for inducting people into your group's Discord guild

* [`cogs/kill.py`](cogs/kill.py): cogs related to the shutdown of TeX-Bot

* [`cogs/make_applicant`](cogs/make_applicant.py): cogs related to making users into applicants

* [`cogs/make_member.py`](cogs/make_member.py): cogs related to making guests into members

* [`cogs/ping.py`](cogs/ping.py): cog to request a [ping](https://wikipedia.org/wiki/Ping-pong_scheme#Internet) response

* [`cogs/remind_me.py`](cogs/remind_me.py): cogs to ask TeX-Bot to send a reminder message at a later date

* [`cogs/send_get_roles_reminders.py`](cogs/send_get_roles_reminders.py): cogs relating to sending reminders, to Discord members, about opt-in roles.
(See [Repeated Tasks Conditions](README.md#repeated-tasks-conditions) for which conditions are required to be met, to execute this task)

* [`cogs/send_introduction_reminders.py`](cogs/send_introduction_reminders.py): cogs relating to sending reminders, to Discord members, about introducing themselves.
(See [Repeated Tasks Conditions](README.md#repeated-tasks-conditions) for which conditions are required to be met, to execute this task)

* [`cogs/source.py`](cogs/source.py): cogs for displaying information about the source-code of this project

* [`cogs/startup.py`](cogs/startup.py): cogs for startup & bot initialisation

* [`cogs/stats/`](cogs/stats): cogs for displaying stats about your group's Discord guild, as well as its channels & Discord members

* [`cogs/strike.py`](cogs/strike.py): cogs for applying moderation actions to Discord members

* [`cogs/write_roles.py`](cogs/write_roles.py): cogs relating to sending the message, that contains all the opt-in roles, into the "#**roles**" channel

## Making Your First Contribution

After you have found an issue which needs solving, it's time to start working on a fix!
However, there are a few guidelines we would like you to follow first.

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

Although there is [a PyCharm plugin](https://github.com/leinardi/mypy-pycharm#mypy-pycharm) to provide GUI control and inline warnings for [mypy](https://mypy-lang.org), it has been rather temperamental recently.
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

## Guides

### Creating a New Cog

Cogs are modular components of TeX-Bot that group related commands and listeners into a single class. To create a new cog, follow these steps:

1. **Create the Cog File**
   - Navigate to the `cogs/` directory.
   - Create a new Python file with a name that reflects the purpose of the cog (e.g., `example_cog.py`).

2. **Define the Cog Class**
   - Import the necessary modules, including `TeXBotBaseCog` from `utils`.
   - Define a class that inherits from `TeXBotBaseCog`.
   - Add a docstring to describe the purpose of the cog.

   Example:
   ```python
   from utils import TeXBotBaseCog

   class ExampleCog(TeXBotBaseCog):
       """A cog for demonstrating functionality."""

       def do_something(arguments):
        print("do something")
   ```

3. **Add Commands and Listeners**
   - Define methods within the class for commands and event listeners.
   - Use decorators like `@discord.slash_command()` or `@TeXBotBaseCog.listener()` to register the callback method to their [interaction](TERMINOLOGY.md#Interactions) type.
   - Include any necessary checks using `CommandChecks` decorators.

   Example:
   ```python
   import discord
   from utils import CommandChecks

    __all__: "Sequence[str]" = (
        "ExampleCog",
    )

   class ExampleCog(TeXBotBaseCog):
       """A cog for demonstrating functionality."""

   ```

4. **Register the Cog**
   - Edit `cogs/__init__.py` to add your new cog class to the list of cogs in the `setup` function.
   - Also, include the cog class in the `__all__` sequence to ensure it is properly exported.

   Example:
   ```python
   from .example_cog import ExampleCog

   __all__: "Sequence[str]" = (
       ...existing cogs...
       "ExampleCog",
   )

   def setup(bot: "TeXBot") -> None:
       """Add all the cogs to the bot, at bot startup."""
       cogs: Iterable[type[TeXBotBaseCog]] = (
           ...existing cogs...
           ExampleCog,
       )
       Cog: type[TeXBotBaseCog]
       for Cog in cogs:
           bot.add_cog(Cog(bot))
   ```

5. **Test the Cog**
   - Run the bot with your changes and ensure the new cog is loaded without errors.
   - Test the commands and listeners to verify they work as expected.

6. **Document the Cog**
   - Add comments and docstrings to explain the functionality of the cog.
   - Update the `CONTRIBUTING.md` file or other relevant documentation if necessary.

### Creating a New Environment Variable

To add a new environment variable to the project, follow these steps:

1. **Define the Variable in development `.env`**
   - Open the `.env` file in the project root directory (or create one if it doesn't exist).
   - Add the new variable in the format `VARIABLE_NAME=value`.
   - Ensure the variable name is descriptive and uses uppercase letters with underscores.

2. **Update `config.py`**
   - Open the `config.py` file.
   - Add a new private setup method in the `Settings` class to validate and load the variable. For example:
     ```python
     @classmethod
     def _setup_new_variable(cls) -> None:
         raw_value: str | None = os.getenv("NEW_VARIABLE")

         if not raw_value or not re.fullmatch(r"<validation_regex>", raw_value):
             raise ImproperlyConfiguredError("NEW_VARIABLE is invalid or missing.")

         cls._settings["NEW_VARIABLE"] = raw_value
     ```
   - Replace `<validation_regex>` with a regular expression to validate the variable's format, if applicable.

3. **Call the Setup Method**
   - Add the new setup method to the `_setup_env_variables` method in `config.py`:
     ```python
     @classmethod
     def _setup_env_variables(cls) -> None:
         if cls._is_env_variables_setup:
             logger.warning("Environment variables have already been set up.")
             return

         cls._settings = {}

         cls._setup_new_variable()
         # Add other setup methods here

         cls._is_env_variables_setup = True
     ```

4. **Document the Variable**
   - Update the `README.md` file under the "Setting Environment Variables" section to include the new variable, its purpose and any valid values.

5. **Test the Variable**
   - Run the bot with your changes and ensure the new variable is loaded correctly.
   - Test edge cases, such as missing, blank or invalid values in the `.env` file, to confirm that error handling functions correctly.

### Creating a Response Button

Response buttons are interactive UI components that allow users to respond to bot messages with predefined actions. To create a response button, follow these steps:

1. **Define the Button Class**
   - Create a new class in your cog file that inherits from `discord.ui.View`.
   - Add button callback response methods using the `@discord.ui.button` decorator.
   - Each button method should define the button's label, a custom response ID and style.

   Example:
   ```python
   from discord.ui import View

   class ConfirmActionView(View):
       """A discord.View containing buttons to confirm or cancel an action."""

       @discord.ui.button(
           label="Yes",
           style=discord.ButtonStyle.green,
           custom_id="confirm_yes",
       )
       async def confirm_yes(self, button: discord.Button, interaction: discord.Interaction) -> None:
           # Handle the 'Yes' button click
           await interaction.response.send_message("Action confirmed.", ephemeral=True)

       @discord.ui.button(
           label="No",
           style=discord.ButtonStyle.red,
           custom_id="confirm_no",
       )
       async def confirm_no(self, button: discord.Button, interaction: discord.Interaction) -> None:
           # Handle the 'No' button click
           await interaction.response.send_message("Action cancelled.", ephemeral=True)
   ```

2. **Send the View with a Message**
   - Use the `view` parameter of the `send` or `respond` method to attach the button view to a message. This could be sent in response to a command, event handler or scheduled task.

   Example:
   ```python
   await ctx.send(
       content="Do you want to proceed?",
       view=ConfirmActionView(),
   )
   ```

3. **Handle Button Interactions**
   - Define logic within each button method to handle user interactions.
   - Use `interaction.response` to send feedback or perform actions based on the button clicked.

4. **Test the Button**
   - Run the bot with your changes and ensure the buttons appear and function as expected.
   - Test edge cases, such as multiple users interacting with the buttons simultaneously.

5. **Document the Button**
   - Add comments and docstrings to explain the purpose and functionality of the button.
   - Update relevant documentation if necessary.

### Creating and Interacting with Django Models

#### Data Protection Consideration

When making changes to the database model, it is essential to consider the data protection implications of these changes. If personal data is being collected, stored or processed, it is essential that this is in compliance with the law. In the UK, the relevant law is the [Data Protection Act 2018](https://www.legislation.gov.uk/ukpga/2018/12/contents). As a general rule, any changes that have data protection implications should be checked and approved by the organisation responsible for running the application.
Django models are used to interact with the database in this project. They allow you to define the structure of your data and provide an API to query and manipulate it. To create and interact with Django models, follow these steps:

1. **Define a Model**
   - Navigate to the `db/core/models/` directory.
   - Create a new Python file with a name that reflects the purpose of the model (e.g., `example_model.py`).
   - If your model is a new property related to each Discord member (E.g. the number of smiley faces of each Discord member, then define a class that inherits from `BaseDiscordMemberWrapper` (found within the `.utils` module within the `db/core/models/` directory).
   - If your model is unrelated to Discord members, then define a class that inherits from `AsyncBaseModel` (also found within the `.utils` module within the `db/core/models/` directory).
   - Add your Django fields to the class to represent the model's data structure.
   - If your model inherits from `BaseDiscordMemberWrapper` then you *must* declare a field called `discord_member` which must be either a Django `ForeignKey` field or a `OneToOneField`, depending upon the relationship between your model and each Discord member.
   - Define the static class string holding the display name for multiple instances of your class (E.g., `INSTANCES_NAME_PLURAL: str = "Members' Smiley Faces"`)

   Example:
   ```python
   from django.db import models

   from .utils import AsyncBaseModel, BaseDiscordMemberWrapper

   class ExampleModel(AsyncBaseModel):
       """A model for demonstrating functionality."""

       INSTANCES_NAME_PLURAL: str = "Example Model objects"

       name = models.CharField(max_length=255)
       created_at = models.DateTimeField(auto_now_add=True)
   class MemberSmileyFaces(BaseDiscordMemberWrapper):
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
        count = models.IntegerField(
            "Number of smiley faces",
            null=False,
            blank=True,
            default=0,
        )

2. **Apply Migrations**
   - Run the following commands to create and apply migrations for your new model:
     ```shell
     uv run manage.py makemigrations
     uv run manage.py migrate
     ```

3. **Query the Model**
   - Use Django's ORM to interact with the model. For example:
     ```python
     from db.core.models.example_model import ExampleModel

     class ExampleCog(TeXBotBaseCog):
         """A cog for demonstrating model access."""

         async def create_example(self, name: str) -> None:
             """Create a new instance of ExampleModel."""
             await ExampleModel.objects.acreate(name=name)

         async def retrieve_examples(self) -> list[ExampleModel]:
             """Retrieve all instances of ExampleModel."""
             return await ExampleModel.objects.all()

         async def filter_examples(self, name: str) -> list[ExampleModel]:
             """Filter instances of ExampleModel by name."""
             return await ExampleModel.objects.filter(name=name)

         async def update_example(self, example: ExampleModel, new_name: str) -> None:
             """Update the name of an ExampleModel instance."""
             example.name = new_name
             await example.asave()

         async def delete_example(self, example: ExampleModel) -> None:
             """Delete an ExampleModel instance."""
             await example.adelete()
     ```

4. **Document the Model**
   - Add comments and docstrings to explain the purpose and functionality of your new model.

### Member Retrieval DB Queries via Hashed Discord ID

To retrieve members from the database using their hashed Discord ID, follow these steps:

1. **Hash the Discord ID**
   - Use a consistent hashing algorithm to hash the Discord ID before storing or querying it in the database.

   Example:
   ```python
   import hashlib

   def hash_discord_id(discord_id: str) -> str:
       return hashlib.sha256(discord_id.encode()).hexdigest()
   ```

2. **Query the Database**
   - A custom filter field is implemented for models that inherit from `BaseDiscordMemberWrapper`, this allows you to filter using the unhashed Discord ID, despite only the hashed Discord ID being stored in the database.

   Example:
   ```python
   from db.core.models.member_smiley_faces import MemberSmileyFaces

   class MyExampleCommandCog(TeXBotBaseCog):
       @tasks.loop(minutes=5)
       async def check_member_smiley_faces(self) -> None:
           member_smiley_faces = await MemberSmileyFaces.objects.filter(discord_id=1234567).afirst()

           if member_smiley_faces:
               print(f"Member's smiley faces found: {member_smiley_faces.discord_member.name}")
           else:
               print("Member's smiley facesnot found.")
   ```

    It is unlikely that you will need to query the `DiscordMember` model directly. Instead, the attributes of the member can be accessed by the relationship between each new Django model to the `DiscordMember` model.

3. **Test the Query**
   - Ensure the query works as expected by testing it with valid and invalid Discord IDs.

4. **Document the Query**
   - Add comments and docstrings to explain the purpose and functionality of the query.
