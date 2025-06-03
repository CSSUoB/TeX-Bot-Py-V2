# TeX-Bot-Py-V2 Terminology

## ["Guild"](https://discord.com/developers/docs/resources/guild) Vs ["Server"](https://wikipedia.org/wiki/Discord#Servers)

Confusingly, [Discord](https://discord.com) uses the term ["guild"](https://discord.com/developers/docs/resources/guild) to refer to a [Discord "server"](https://wikipedia.org/wiki/Discord#Servers), when communicating with developers.
Therefore, the same terminology (["guild"](https://discord.com/developers/docs/resources/guild)) will be used across all documentation in this project.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/guild) & [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#discord.Guild) for more information.)

The term "main guild" is used throughout the code in this repository to refer specifically to your community group's main [Discord guild](https://discord.com/developers/docs/resources/guild).


## [Interactions](https://discord.com/developers/docs/interactions/overview)

Interactions in Discord are a way for bots to communicate with users in a structured and interactive manner. They are the initial entry point to allow users to begin interacting with the bot. (Note that a Discord bot's functionality could also be triggered via non-interaction methods like scheduled tasks or event handlers.) The primary types of interactions are:

1. **Application Commands**: These include Slash Commands, Message Commands, and User Commands. They are predefined commands that users can invoke to perform specific actions.
2. **Message Components**: These are interactive elements like buttons, select menus, and modals that can be attached to messages to provide a richer user experience.
3. **Modal Submissions**: These are forms that users can fill out and submit, allowing bots to collect structured input from users, though TeX-Bot does not currently make use of these.

For more details, refer to the [Discord Developer Documentation on Interactions](https://discord.com/developers/docs/interactions/overview).


## [Application Commands](https://discord.com/developers/docs/interactions/application-commands)


An [Application Command](https://discord.com/developers/docs/interactions/application-commands) can be a [Slash Command](#slash-commands), [Message Command](#message-commands) or [User Command](#user-commands).

Bots are limited to only 100 [Slash Commands](#slash-commands), 5 [Message Commands](#message-commands) and 5 [User Commands](#user-commands).

The primary difference is the way these commands are triggered. [Slash Commands](#slash-commands) are triggered by sending a message into the chat, while both [User Commands](#user-commands) and [Message Commands](#message-commands) are triggered via a UI context menu provided by right-clicking on a [User](https://discord.com/developers/docs/resources/user) or [Message](https://discord.com/developers/docs/resources/message) respectively.


### [Slash Commands](https://discord.com/developers/docs/interactions/application-commands#slash-commands)


Slash commands, also known as `CHAT_INPUT` commands are executed via sending a chat message and are made up of a name, description and a set of options. These can be defined using the `@discord.slash_command()` decorator.


For example usages, check the [Guides section](CONTRIBUTING.md#Guides) of the [CONTRIBUTING.md document](CONTRIBUTING.md).


### Context Commands

#### [Message Commands](https://discord.com/developers/docs/interactions/application-commands#message-commands)


Message-context commands, are executed via right-clicking on a [Discord *Message*](https://discord.com/developers/docs/resources/message), clicking "Apps", then selecting the command from the menu. The interaction callback method is provided information about which message was clicked, along with which user clicked it.

The main difference between [Context Commands](#context-commands) and [Slash Commands](#slash-commands) is that [Context Commands](#context-commands) do not take user defined arguments and are limited to the [Message](https://discord.com/developers/docs/resources/message) that the command is issued on and the context which is passed along side it.


#### [User Commands](https://discord.com/developers/docs/interactions/application-commands#user-commands)



## "User" Vs "Member" Vs "Guest"

### [Discord Objects](https://discord.com/developers/docs)

In the context of [Discord](https://discord.com) itself, a ["user"](https://discord.com/developers/docs/resources/user) object represents a [Discord](https://discord.com) account not connected to any specific [guild](https://discord.com/developers/docs/resources/guild).
Therefore, it can be [messaged via DM](https://dictionary.com/browse/dm) or be retrieved via its [snowflake ID](https://discord.com/developers/docs/reference#snowflakes), but little else can be done with it.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/user) & [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#users) for more information.)

In contrast, a [Discord "member" object](https://discord.com/developers/docs/resources/guild#guild-member-object) is a [user](https://discord.com/developers/docs/resources/user) attached to a specific [guild](https://discord.com/developers/docs/resources/guild).
Therefore, it can have [roles](https://discord.com/developers/docs/topics/permissions#role-object), be [banned](https://discord.com/developers/docs/resources/guild#ban-object) & have many other actions applied to it.
(See [the Discord developer docs](https://discord.com/developers/docs/resources/guild#guild-member-object) & [Pycord's docs](https://docs.pycord.dev/en/stable/api/models.html#discord.Member) for more information.)

### Community Group Membership

In the context of your community group's membership structure, a "member" is a person that has purchased a membership to join your community group.
This is in contrast to a "guest", which is a person that has not purchased a membership.
Guests often can only attend events that are open to anyone (i.e. **not** members only), and have limited communication/perks within your [Discord guild](https://discord.com/developers/docs/resources/guild).
Some commands may require you to create [roles](https://discord.com/developers/docs/topics/permissions#role-object) within your [Discord guild](https://discord.com/developers/docs/resources/guild), to differentiate between these different types of users.

### Other Uses

In some other contexts, the term "user" may be used to refer to any person/organisation making use of this project.
(E.g. the description within [the "Error Codes" section](#error-codes).)
