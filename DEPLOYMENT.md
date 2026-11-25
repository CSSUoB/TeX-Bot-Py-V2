# TeX-Bot-Py-V2 Deployment

> [!NOTE]
> Please familiarise yourself with all the terms defined in [TERMINOLOGY.md](TERMINOLOGY.md) before continuing, to prevent any confusion.

## Deploying in Production

The only supported way to deploy TeX-Bot in production is by using our pre-built [docker container](https://docs.docker.com/resources/what-container).
It can be pulled from the [GitHub Container Registry](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry) with this identifier: [`ghcr.io/CSSUoB/tex-bot-py-v2:latest`](https://github.com/CSSUoB/TeX-Bot-Py-V2/pkgs/container/tex-bot-py-v2).
([Here is an introduction](https://docs.docker.com/get-started/08_using_compose) on how to use a [docker-compose deployment](https://docs.docker.com/compose).)
See [**Versioning**](README.md#versioning) for the full list of available version tags for each release.

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
It's also handy if you have an empty [Discord guild](TERMINOLOGY.md#guild-vs-server) for you to test in.

The correct [invite URL](https://docs.pycord.dev/en/stable/discord.html#inviting-your-bot) will be displayed to you in the console the first time you run the bot (or if you set a high verbosity log level)

### Setting [Environment Variables](https://wikipedia.org/wiki/Environment_variable)

You'll also need to set a number of [environment variables](https://wikipedia.org/wiki/Environment_variable) before running TeX-Bot:

* `DISCORD_BOT_TOKEN`: The [Discord bot secret token](https://itexus.com/glossary/discord-bot-token) for the [instance of TeX-Bot](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts) you created.
  * The [Discord bot token](https://itexus.com/glossary/discord-bot-token) is available on [your bot's page in the Discord Developer Portal](https://discord.com/developers/applications).

* `DISCORD_GUILD_ID`: The [ID](https://discord.com/developers/docs/reference#snowflakes) of your community group's [Discord guild](TERMINOLOGY.md#guild-vs-server).

* `DISCORD_LOG_CHANNEL_WEBHOOK_URL`: The [webhook URL](https://support.discord.com/hc/articles/228383668-Intro-to-Webhooks) of the [Discord text channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel) where error log messages should be sent.
  * This setting is optional.
    Error logs will **always** be sent to the [console](https://wikipedia.org/wiki/Terminal_emulator), this setting just allows them to also be sent to a [Discord log channel](https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel).

* `ORGANISATION_ID`: Your SU platform organisation ID.
  This is used to dynamically create the members list and other needed URLs.

* `SU_PLATFORM_ACCESS_COOKIE`: The SU platform [access session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie).
  * This [session cookie](https://wikipedia.org/wiki/HTTP_cookie#Session_cookie) will [authenticate](https://wikipedia.org/wiki/Authentication) TeX-Bot to view your group's members list on the SU platform, as if it were [logged in to the website](https://wikipedia.org/wiki/Login_session) as a Committee member.
  * This can be [extracted from your web-browser](https://wikihow.com/View-Cookies), after logging in to view your members list yourself.
    It will most likely be listed as a [cookie](https://wikipedia.org/wiki/HTTP_cookie) named `.AspNet.SharedCookie`.
  * If you wish to test TeX-Bot with the SU platform-access disabled, a dummy value of 512 `0` characters can be used.
    Note that this will cause many commands and scheduled tasks to fail when they are used at runtime.

* `MODERATION_DOCUMENT_URL`: The URL of your group's [Discord guild](TERMINOLOGY.md#guild-vs-server) moderation document.

You can put these [variables](https://wikipedia.org/wiki/Environment_variable) in a [`.env` file](https://blog.bitsrc.io/a-gentle-introduction-to-env-files-9ad424cc5ff4) in the root folder, as [python-dotenv](https://saurabh-kumar.com/python-dotenv) is used to collect all [environment variables](https://wikipedia.org/wiki/Environment_variable).
There is an [`.env.example` file](.env.example) in the repo that you can rename and populate.

There are also many other configuration settings that can be changed to alter the behaviour of TeX-Bot.
These are all listed in [the `.env.example` file](.env.example), along with the behaviours that will be affected.

Any [variables](https://wikipedia.org/wiki/Environment_variable), in [the `.env.example` file](.env.example), marked with `# !!REQUIRED!!` must be set before running TeX-Bot.
All other [variables](https://wikipedia.org/wiki/Environment_variable) are optional and their default values are shown as the example value for each variable in [the `.env.example` file](.env.example).

### Running The Bot

Once everything is set up, you should be able to execute the following command to automatically run TeX-Bot & connect it to your [Discord guild](TERMINOLOGY.md#guild-vs-server):

```shell
uv run -m main
```

Any pending database migrations are applied automatically each time TeX-Bot starts up.
