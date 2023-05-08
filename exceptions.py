from typing import Collection, Iterable


def format_does_not_exist_with_dependant_commands(value: str, does_not_exist_type: str, dependant_commands: Collection[str]) -> str:
    if len(dependant_commands) == 0:
        raise ValueError("Argument \"dependant_commands\" cannot be empty collection.")

    formatted_dependant_commands: str = ""

    if len(dependant_commands) == 1:
        formatted_dependant_commands += f"\"/{next(iter(dependant_commands))}\" command"
    else:
        index: int
        dependant_command: str
        for index, dependant_command in enumerate(dependant_commands):
            formatted_dependant_commands += f"\"/{dependant_command}\""

            if index < len(dependant_commands) - 2:
                formatted_dependant_commands += ", "
            elif index == len(dependant_commands) - 2:
                formatted_dependant_commands += " & "

        formatted_dependant_commands += " commands"

    formatted_dependant_commands += "."

    if does_not_exist_type == "channel":
        value = f"#{value}"

    return f"""\"{value}\" {does_not_exist_type} must exist in order to use the {formatted_dependant_commands}"""


class ImproperlyConfigured(Exception):
    """
        Exception class to raise when environment variables are not correctly
        supplied.
    """

    pass


class GuildDoesNotExist(ValueError):
    DEFAULT_MESSAGE: str = "Server with given ID does not exist"

    def __init__(self, message: str | None = None, guild_id: int | None = None) -> None:
        self.guild_id: int | None = guild_id

        if guild_id and not message:
            message = f"Server with ID \"{guild_id}\" does not exist."

        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        if self.guild_id and str(self.guild_id) not in self.message:
            return f"{self.message} (guild_id={repr(self.guild_id)})"

        else:
            return self.message


class RoleDoesNotExist(ValueError):
    DEFAULT_MESSAGE: str = "Role with given name does not exist"

    def __init__(self, message: str | None = None, role_name: str | None = None, dependant_commands: Collection[str] | None = None) -> None:
        self.role_name: str | None = role_name
        self.dependant_commands: Iterable[str] | None = dependant_commands

        if role_name and not message:
            if dependant_commands:
                message = format_does_not_exist_with_dependant_commands(role_name, "role", dependant_commands)
            else:
                message = f"Role with name \"{role_name}\" does not exist."

        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        if self.role_name is None or self.role_name not in self.message:
            return f"{self.message} (role_name={repr(self.role_name)}, dependant_commands={repr(self.dependant_commands)})"

        else:
            return self.message


class CommitteeRoleDoesNotExist(RoleDoesNotExist):
    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, role_name="Committee", dependant_commands={"writeroles", "editmessage", "induct"})


class GuestRoleDoesNotExist(RoleDoesNotExist):
    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, role_name="Guest", dependant_commands={"induct"})


class ChannelDoesNotExist(ValueError):
    DEFAULT_MESSAGE: str = "Channel with given name does not exist"

    def __init__(self, message: str | None = None, channel_name: str | None = None, dependant_commands: Collection[str] | None = None) -> None:
        self.channel_name: str | None = channel_name
        self.dependant_commands: Iterable[str] | None = dependant_commands

        if channel_name and not message:
            if dependant_commands:
                message = format_does_not_exist_with_dependant_commands(channel_name, "channel", dependant_commands)
            else:
                message = f"Channel with name \"{channel_name}\" does not exist."

        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        if self.channel_name is None or self.channel_name not in self.message:
            return f"{self.message} (channel_name={repr(self.channel_name)}, dependant_commands={repr(self.dependant_commands)})"

        else:
            return self.message


class RolesChannelDoesNotExist(ChannelDoesNotExist):
    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, channel_name="roles", dependant_commands={"writeroles", "induct"})


class GeneralChannelDoesNotExist(ChannelDoesNotExist):
    def __init__(self, message: str | None = None) -> None:
        # noinspection SpellCheckingInspection
        super().__init__(message, channel_name="general", dependant_commands={"induct"})
