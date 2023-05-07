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

    def __init__(self, message: str | None = None, role_name: str | None = None) -> None:
        self.role_name: str | None = role_name

        if role_name and not message:
            message = f"Role with name \"{role_name}\" does not exist."

        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        if self.role_name and self.role_name not in self.message:
            return f"{self.message} (role_name={repr(self.role_name)})"

        else:
            return self.message


class ChannelDoesNotExist(ValueError):
    DEFAULT_MESSAGE: str = "Channel with given name does not exist"

    def __init__(self, message: str | None = None, channel_name: str | None = None) -> None:
        self.channel_name: str | None = channel_name

        if channel_name and not message:
            message = f"Channel with name \"{channel_name}\" does not exist."

        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        if self.channel_name and self.channel_name not in self.message:
            return f"{self.message} (channel_name={repr(self.channel_name)})"

        else:
            return self.message
