# Contributing

A big welcome and thank you for considering contributing to CSS' open source projects! We welcome anybody who wants to contribute, and we actively encourage everyone to do so, especially if you have never contributed before.

## Quick Links

* [Getting started](#Getting-Started)
* [Using the issue tracker](#Using-the-Issue-Tracker)
* [Project structure](#Project-Structure)
* [Making your first contribution](#Making-Your-First-Contribution)
* [Guidance](#Guidance)

## Getting Started

If you have never used git before, we would recommend that you read the [GitHub's Getting Started guide](https://guides.github.com/introduction/getting-started-with-git/). Additionally, linked below are some helpful resources:

* [GitHub git guides](https://github.com/git-guides)
* [git - the simple guide](https://rogerdudler.github.io/git-guide/)
* [Getting Git Right (Atlassian)](https://www.atlassian.com/git/)

If you are new to contributing to open-source projects on GitHub, the general workflow is as follows:

1. Fork this repository and clone it
2. Create a branch off main
3. Make your changes and commit them
4. Push your local branch to your remote fork
5. Open a new pull request on GitHub

We recommend also reading the following if you're unsure or not confident:

* https://makeapullrequest.com/
* https://www.firsttimersonly.com/

## Using the Issue Tracker

We use GitHub issues to track bugs and feature requests. If you find an issue with the bot, the best place to report it is through the issue tracker. If you are looking for issues to contribute code to, it's a good idea to look at the [issues labelled "good-first-issue"](https://github.com/CSSUoB/TeX-Bot-Py/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Agood-first-issue)!

When submitting an issue, please be as descriptive as possible. If you are submitting a bug report, please include the steps to reproduce the bug, and the environment it is in. If you are submitting a feature request, please include the steps to implement the feature.

## Project Structure

This bot is written in Python using [Pycord](https://pycord.dev) and uses [Discord's slash commands](https://support.discord.com/hc/en-gb/articles/1500000368501-Slash-Commands-FAQ). We would recommend being somewhat familiar with the library and language terminology before contributing.

* `main.py`: is the main entrypoint to instantiate the bot object & run it
* `exceptions.py`: contains common exception super-classes that may be raised when certain errors occur
* `setup.py`: retrieves the environment variables & populates the correct values into the `settings` attribute
* `utils.py`: contains common utility classes & functions used by the top-level modules
* `cogs/commands.py`: contains slash commands & user context-menu commands
* `cogs/events.py`: contains event listeners
* `cogs/tasks.py`: contains repeating tasks
* `cogs/utils.py`: contains common utility classes & functions used by the other cog modules
* `db.core.models`: contains all the database ORM models to interact with storing information longer-term (between individual command events)

## Making Your First Contribution

After you have found an issue which needs solving, it's time to start working on a fix! However, there are a few guidelines we would like you to follow first.

### Code Style

In general, follow the formatting in the file you are editing. We also have a [Pycharm `codeStyleConfig.xml`](https://www.jetbrains.com/help/pycharm/configuring-code-style.html) file and [mypy](https://www.mypy-lang.org/) type checking which you can configure your IDE to use.

### Git Commit Messages

Commit messages should be written in the imperative present tense. For example, "Fix bug #1".

Commit subjects should start with a capital letter and **not** end in a full-stop

Additionally, we request that you keep the commit subject under 80 characters for a comfortable viewing experience on GitHub and other git tools. If you need more, please use the body of the commit. (See [Robert Painsi's Commit Message Guidelines](https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53) for how to write good commit messages.)

For example:

```
Fix TeX becoming sentient

<more detailed description here>
```

### What Happens Next?

Once you have made your changes, please describe them in your pull request in full. We will then review them and communicate with you on GitHub. We may ask you to change a few things, so please do check GitHub or your emails frequently.

After that, that's it! You've made your first contribution. 🎉

## License

Please note that any contributions you make will be made under the terms of the [Apache Licence 2.0](https://github.com/CSSUoB/TeX-Bot-Py/blob/main/LICENSE).

## Guidance

We aim to get more people involved with our projects, and help build members' confidence in using git and contributing to open-source. If you see an error, we encourage you to **be bold** and fix it yourself, rather than just raising an issue. If you are stuck, need help, or have a question, the best place to ask is on our Discord.

Happy contributing!
