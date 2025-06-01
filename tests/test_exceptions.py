"""Automated test suite for all custom exceptions within `exceptions.py`."""

from typing import TYPE_CHECKING, override

import pytest
from typed_classproperties import classproperty

from exceptions import (
    ChannelDoesNotExistError,
    DiscordMemberNotInMainGuildError,
    GuildDoesNotExistError,
    ImproperlyConfiguredError,
    InvalidMessagesJSONFileError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
    RoleDoesNotExistError,
)
from exceptions.base import BaseDoesNotExistError, BaseTeXBotError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Final


class TestImproperlyConfiguredError:
    """Test case to unit-test the `ImproperlyConfiguredError` exception."""

    @pytest.mark.parametrize("test_exception_message", ("Error 1 occurred",))
    def test_message(self, test_exception_message: str) -> None:
        """Test that the custom error message is used in the `__str__` representation."""
        assert str(ImproperlyConfiguredError(test_exception_message)) == test_exception_message

    @pytest.mark.parametrize("test_exception_message", ("Error 1 occurred",))
    def test_message_when_raised(self, test_exception_message: str) -> None:
        """Test that the custom error message is shown when the exception is raised."""
        with pytest.raises(ImproperlyConfiguredError, match=test_exception_message):
            raise ImproperlyConfiguredError(test_exception_message)


class TestBaseTeXBotError:
    """Test case to unit-test the `BaseTeXBotError` exception."""

    class _DefaultMessageBaseTeXBotErrorSubclass(BaseTeXBotError):  # noqa: N818
        """
        Custom subclass implementation of `BaseTeXBotError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has a `DEFAULT_MESSAGE` set.
        """

        @classproperty
        @override
        def DEFAULT_MESSAGE(cls) -> str:
            """The message to be displayed alongside this exception class if not provided."""
            return "Error 1 occurred"

    class _AttributesBaseTeXBotErrorSubclass(_DefaultMessageBaseTeXBotErrorSubclass):
        """
        Custom subclass implementation of `BaseTeXBotError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has a new instance attribute (compared to the parent base class).
        """

        def __init__(
            self, message: str | None = None, test_attribute_value: object | None = None
        ) -> None:
            """Initialize a new exception with the given error message."""
            self.test_attribute: object | None = test_attribute_value

            super().__init__(message=message)

    @pytest.mark.parametrize(
        "test_base_texbot_error_subclass",
        (
            _DefaultMessageBaseTeXBotErrorSubclass(),
            _DefaultMessageBaseTeXBotErrorSubclass(message=None),
            _DefaultMessageBaseTeXBotErrorSubclass(message=""),
        ),
    )
    def test_default_message(self, test_base_texbot_error_subclass: BaseTeXBotError) -> None:
        """Test that the class' default error message is shown, when no custom message."""
        assert (
            test_base_texbot_error_subclass.message
            == self._DefaultMessageBaseTeXBotErrorSubclass.DEFAULT_MESSAGE
        )
        assert (
            str(test_base_texbot_error_subclass)
            == self._DefaultMessageBaseTeXBotErrorSubclass.DEFAULT_MESSAGE
        )

    @pytest.mark.parametrize("test_exception_message", ("Other test error occurred",))
    def test_custom_message(self, test_exception_message: str) -> None:
        """Test that the custom error message is shown, when given."""
        assert (
            self._DefaultMessageBaseTeXBotErrorSubclass(test_exception_message).message
            == test_exception_message
        )
        assert (
            str(self._DefaultMessageBaseTeXBotErrorSubclass(test_exception_message))
            == test_exception_message
        )

    @pytest.mark.parametrize(
        "test_attributes_base_texbot_error_subclass",
        (
            _AttributesBaseTeXBotErrorSubclass(),
            _AttributesBaseTeXBotErrorSubclass(test_attribute_value=None),
            _AttributesBaseTeXBotErrorSubclass(test_attribute_value=7),
        ),
    )
    def test_repr_with_attributes(
        self, test_attributes_base_texbot_error_subclass: _AttributesBaseTeXBotErrorSubclass
    ) -> None:
        """Test that the exception message contains any instance attributes."""
        assert (
            f"test_attribute={test_attributes_base_texbot_error_subclass.test_attribute!r}"
            in repr(test_attributes_base_texbot_error_subclass)
        )


class TestBaseErrorWithErrorCode:
    """
    Test case to unit-test the `BaseErrorWithErrorCode` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `BaseErrorWithErrorCode` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestBaseDoesNotExistError:
    """Test case to unit-test the `BaseDoesNotExistError` exception."""

    class _NoDependantsBaseDoesNotExistErrorSubclass(BaseDoesNotExistError):  # noqa: N818
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has no dependent commands, tasks or events.
        """

        @classproperty
        @override
        def DEFAULT_MESSAGE(cls) -> str:
            """The message to be displayed alongside this exception class if not provided."""
            return "Error 1 occurred"

        @classproperty
        @override
        def ERROR_CODE(cls) -> str:
            """The unique error code for users to tell admins about an error that occurred."""
            return "E1"

        @classproperty
        @override
        def DOES_NOT_EXIST_TYPE(cls) -> str:
            """The name of the Discord entity that this `DoesNotExistError` is attached to."""
            return "object_type"

    class _OneDependentCommandBaseDoesNotExistErrorSubclass(
        _NoDependantsBaseDoesNotExistErrorSubclass
    ):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has one command-dependent.
        """

        @classproperty
        @override
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """
            return frozenset(("command_1",))

    class _MultipleDependentCommandsBaseDoesNotExistErrorSubclass(
        _NoDependantsBaseDoesNotExistErrorSubclass
    ):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has multiple dependent commands.
        """

        @classproperty
        @override
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """
            return frozenset(("command_1", "command_2", "command_3"))

    class _OneDependentTaskBaseDoesNotExistErrorSubclass(
        _NoDependantsBaseDoesNotExistErrorSubclass
    ):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has one task-dependent.
        """

        @classproperty
        @override
        def DEPENDENT_TASKS(cls) -> frozenset[str]:
            """
            The set of names of bot tasks that require this Discord entity.

            This set being empty could mean that all bot tasks require this Discord entity,
            or no bot tasks require this Discord entity.
            """
            return frozenset(("task_1",))

    class _MultipleDependentTasksBaseDoesNotExistErrorSubclass(
        _NoDependantsBaseDoesNotExistErrorSubclass
    ):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has multiple dependent tasks.
        """

        @classproperty
        @override
        def DEPENDENT_TASKS(cls) -> frozenset[str]:
            """
            The set of names of bot tasks that require this Discord entity.

            This set being empty could mean that all bot tasks require this Discord entity,
            or no bot tasks require this Discord entity.
            """
            return frozenset(("task_1", "task_2", "task_3"))

    class _OneDependentEventBaseDoesNotExistErrorSubclass(
        _NoDependantsBaseDoesNotExistErrorSubclass
    ):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has one event dependent.
        """

        @classproperty
        @override
        def DEPENDENT_EVENTS(cls) -> frozenset[str]:
            """
            The set of names of bot events that require this Discord entity.

            This set being empty could mean that all bot events require this Discord entity,
            or no bot events require this Discord entity.
            """
            return frozenset(("event_1",))

    class _MultipleDependentEventsBaseDoesNotExistErrorSubclass(
        _NoDependantsBaseDoesNotExistErrorSubclass
    ):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has multiple dependent events.
        """

        @classproperty
        @override
        def DEPENDENT_EVENTS(cls) -> frozenset[str]:
            """
            The set of names of bot events that require this Discord entity.

            This set being empty could mean that all bot events require this Discord entity,
            or no bot events require this Discord entity.
            """
            return frozenset(("event_1", "event_2", "event_3"))

    class _ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass(
        _NoDependantsBaseDoesNotExistErrorSubclass
    ):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass whose `DOES_NOT_EXIST_TYPE` is a channel.
        """

        @classproperty
        @override
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """
            return frozenset(("command_1",))

        @classproperty
        @override
        def DOES_NOT_EXIST_TYPE(cls) -> str:
            """The name of the Discord entity that this `DoesNotExistError` is attached to."""
            return "channel"

    def test_get_formatted_message_with_no_dependants(self) -> None:
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        that has either no dependent commands, events or tasks.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the list of dependent command names separated by "," (comma) characters.
        """
        with pytest.raises(ValueError, match="no dependants"):
            self._NoDependantsBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier="object_1",
            )

    @pytest.mark.parametrize(
        "dependent_commands_base_does_not_exist_error_subclass",
        (
            _OneDependentCommandBaseDoesNotExistErrorSubclass,
            _MultipleDependentCommandsBaseDoesNotExistErrorSubclass,
        ),
    )
    @pytest.mark.parametrize("test_non_existant_object_identifier", ("object_1",))
    def test_get_formatted_message_with_dependent_commands(
        self,
        dependent_commands_base_does_not_exist_error_subclass: type[
            _NoDependantsBaseDoesNotExistErrorSubclass
        ],
        test_non_existant_object_identifier: str,
    ) -> None:
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        that has either one, or multiple dependent commands.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the list of dependent command names separated by "," (comma) characters.
        """
        FORMATTED_MESSAGE: Final[str] = (
            dependent_commands_base_does_not_exist_error_subclass.get_formatted_message(
                non_existent_object_identifier=test_non_existant_object_identifier,
            )
        )

        assert (
            f'"{test_non_existant_object_identifier}" '
            f"{dependent_commands_base_does_not_exist_error_subclass.DOES_NOT_EXIST_TYPE} "
            f"must exist"
        ) in FORMATTED_MESSAGE

        if len(dependent_commands_base_does_not_exist_error_subclass.DEPENDENT_COMMANDS) == 1:
            assert (
                "the "
                f"""\"/{
                    next(
                        iter(
                            dependent_commands_base_does_not_exist_error_subclass.DEPENDENT_COMMANDS
                        )
                    )
                }\" """
                "command"
            ) in FORMATTED_MESSAGE

        elif len(dependent_commands_base_does_not_exist_error_subclass.DEPENDENT_COMMANDS) > 1:
            DEPENDENT_COMMANDS: Final[Iterator[str]] = iter(
                dependent_commands_base_does_not_exist_error_subclass.DEPENDENT_COMMANDS,
            )

            assert (
                f'the "/{next(DEPENDENT_COMMANDS)}", "/{next(DEPENDENT_COMMANDS)}" & '
                f'"/{next(DEPENDENT_COMMANDS)}" commands'
            ) in FORMATTED_MESSAGE

        else:
            raise NotImplementedError

    @pytest.mark.parametrize(
        "dependent_tasks_base_does_not_exist_error_subclass",
        (
            _OneDependentTaskBaseDoesNotExistErrorSubclass,
            _MultipleDependentTasksBaseDoesNotExistErrorSubclass,
        ),
    )
    @pytest.mark.parametrize("test_non_existant_object_identifier", ("object_1",))
    def test_get_formatted_message_with_dependent_tasks(
        self,
        dependent_tasks_base_does_not_exist_error_subclass: type[
            _NoDependantsBaseDoesNotExistErrorSubclass
        ],
        test_non_existant_object_identifier: str,
    ) -> None:
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        that has either one, or multiple dependent tasks.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the list of dependent task names separated by "," (comma) characters.
        """
        FORMATTED_MESSAGE: Final[str] = (
            dependent_tasks_base_does_not_exist_error_subclass.get_formatted_message(
                non_existent_object_identifier=test_non_existant_object_identifier,
            )
        )

        assert (
            f'"{test_non_existant_object_identifier}" '
            f"{dependent_tasks_base_does_not_exist_error_subclass.DOES_NOT_EXIST_TYPE} "
            f"must exist"
        ) in FORMATTED_MESSAGE

        if len(dependent_tasks_base_does_not_exist_error_subclass.DEPENDENT_TASKS) == 1:
            assert (
                "the "
                f"""\"{
                    next(
                        iter(
                            dependent_tasks_base_does_not_exist_error_subclass.DEPENDENT_TASKS
                        )
                    )
                }\" """
                "task"
            ) in FORMATTED_MESSAGE

        elif len(dependent_tasks_base_does_not_exist_error_subclass.DEPENDENT_TASKS) > 1:
            DEPENDENT_TASKS: Final[Iterator[str]] = iter(
                dependent_tasks_base_does_not_exist_error_subclass.DEPENDENT_TASKS,
            )

            assert (
                f'the "{next(DEPENDENT_TASKS)}", "{next(DEPENDENT_TASKS)}" & '
                f'"{next(DEPENDENT_TASKS)}" tasks'
            ) in FORMATTED_MESSAGE

        else:
            raise NotImplementedError

    @pytest.mark.parametrize(
        "dependent_events_base_does_not_exist_error_subclass",
        (
            _OneDependentEventBaseDoesNotExistErrorSubclass,
            _MultipleDependentEventsBaseDoesNotExistErrorSubclass,
        ),
    )
    @pytest.mark.parametrize("test_non_existant_object_identifier", ("object_1",))
    def test_get_formatted_message_with_dependent_events(
        self,
        dependent_events_base_does_not_exist_error_subclass: type[
            _NoDependantsBaseDoesNotExistErrorSubclass
        ],
        test_non_existant_object_identifier: str,
    ) -> None:
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        that has either one, or multiple dependent events.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the list of dependent event names separated by "," (comma) characters.
        """
        FORMATTED_MESSAGE: Final[str] = (
            dependent_events_base_does_not_exist_error_subclass.get_formatted_message(
                non_existent_object_identifier=test_non_existant_object_identifier,
            )
        )

        assert (
            f'"{test_non_existant_object_identifier}" '
            f"{dependent_events_base_does_not_exist_error_subclass.DOES_NOT_EXIST_TYPE} "
            f"must exist"
        ) in FORMATTED_MESSAGE

        if len(dependent_events_base_does_not_exist_error_subclass.DEPENDENT_EVENTS) == 1:
            assert (
                "the "
                f"""\"{
                    next(
                        iter(
                            dependent_events_base_does_not_exist_error_subclass.DEPENDENT_EVENTS
                        )
                    )
                }\" """
                "event"
            ) in FORMATTED_MESSAGE

        elif len(dependent_events_base_does_not_exist_error_subclass.DEPENDENT_EVENTS) > 1:
            DEPENDENT_EVENTS: Final[Iterator[str]] = iter(
                dependent_events_base_does_not_exist_error_subclass.DEPENDENT_EVENTS,
            )

            assert (
                f'the "{next(DEPENDENT_EVENTS)}", "{next(DEPENDENT_EVENTS)}" & '
                f'"{next(DEPENDENT_EVENTS)}" events'
            ) in FORMATTED_MESSAGE

        else:
            raise NotImplementedError

    @pytest.mark.parametrize("test_non_existant_object_identifier", ("object_1",))
    def test_get_formatted_message_with_channel_does_not_exist_type(
        self, test_non_existant_object_identifier: str
    ) -> None:
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        whose `DOES_NOT_EXIST_TYPE` is a Discord channel.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the Discord channel name prefixed by a "#" (hashtag) character,
        as well as the word "channel".
        """
        assert (
            f'"#{test_non_existant_object_identifier}" '
            f"""{
                self._ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE
            } """
            "must exist"
        ) in self._ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass.get_formatted_message(
            non_existent_object_identifier=test_non_existant_object_identifier,
        )


class TestRulesChannelDoesNotExist:
    """
    Test case to unit-test the `RulesChannelDoesNotExist` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `RulesChannelDoesNotExist` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestDiscordMemberNotInMainGuildError:
    """Test case to unit-test the `DiscordMemberNotInMainGuildError` exception."""

    @pytest.mark.parametrize("test_user_id", (99999,))
    def test_user_id_in_repr(self, test_user_id: int) -> None:
        """Test that the exception message contains the given Discord user ID."""
        assert f"user_id={test_user_id!r}" in repr(
            DiscordMemberNotInMainGuildError(user_id=test_user_id)
        )


class TestEveryoneRoleCouldNotBeRetrievedError:
    """
    Test case to unit-test the `EveryoneRoleCouldNotBeRetrievedError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `EveryoneRoleCouldNotBeRetrievedError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestInvalidMessagesJSONFileError:
    """Test case to unit-test the `InvalidMessagesJSONFileError` exception."""

    @pytest.mark.parametrize("test_dict_key", ("key_1",))
    def test_dict_key_in_repr(self, test_dict_key: str) -> None:
        """Test that the exception message contains the given dict key."""
        assert f"dict_key={test_dict_key!r}" in repr(
            InvalidMessagesJSONFileError(dict_key=test_dict_key)
        )


class TestMessagesJSONFileMissingKeyError:
    """Test case to unit-test the `MessagesJSONFileMissingKeyError` exception."""

    @pytest.mark.parametrize("test_missing_key", ("key_1",))
    def test_missing_key_in_repr(self, test_missing_key: str) -> None:
        """Test that the exception message contains the given JSON file missing key name."""
        assert f"dict_key={test_missing_key!r}" in repr(
            MessagesJSONFileMissingKeyError(missing_key=test_missing_key)
        )


class TestMessagesJSONFileValueError:
    """Test case to unit-test the `MessagesJSONFileValueError` exception."""

    @pytest.mark.parametrize("test_json_file_invalid_name", ("value_1",))
    def test_invalid_value_in_repr(self, test_json_file_invalid_name: str) -> None:
        """Test that the exception message contains the given invalid JSON file value."""
        assert f"invalid_value={test_json_file_invalid_name!r}" in repr(
            MessagesJSONFileValueError(invalid_value=test_json_file_invalid_name)
        )


class TestStrikeTrackingError:
    """
    Test case to unit-test the `StrikeTrackingError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `StrikeTrackingError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestGuildDoesNotExistError:
    """Test case to unit-test the `GuildDoesNotExistError` exception."""

    @pytest.mark.parametrize("test_guild_id", (99999,))
    def test_guild_id_in_repr(self, test_guild_id: int) -> None:
        """Test that the exception message contains the given Discord guild ID."""
        assert f"guild_id={test_guild_id!r}" in repr(
            GuildDoesNotExistError(guild_id=test_guild_id)
        )

    @pytest.mark.parametrize("test_guild_id", (99999,))
    def test_default_message_with_guild_id(self, test_guild_id: int) -> None:
        """
        Test that the exception message contains the default error message.

        This test instantiates the GuildDoesNotExistError exception
        with a specific Discord guild ID,
        so the default error message should also contain the given Discord guild ID.
        """
        assert f"ID '{test_guild_id}'" in str(GuildDoesNotExistError(guild_id=test_guild_id))

    def test_default_message_without_guild_id(self) -> None:
        """
        Test that the exception message contains the default error message.

        This test instantiates the GuildDoesNotExistError exception
        without a specific Discord guild ID,
        so the default error message should just contain "given ID".
        """
        assert "given ID" in str(GuildDoesNotExistError())

    def test_error_code(self) -> None:
        """Test that the error code is set correctly."""
        assert "E1011" in (GuildDoesNotExistError().ERROR_CODE)


class TestRoleDoesNotExistError:
    """Test case to unit-test the `RoleDoesNotExistError` exception."""

    class _RoleDoesNotExistErrorSubclass(RoleDoesNotExistError):  # noqa: N818
        """Custom subclass implementation of `RoleDoesNotExistError`, for testing purposes."""

        @classproperty
        @override
        def ERROR_CODE(cls) -> str:
            """The unique error code for users to tell admins about an error that occurred."""
            return "E1"

        @classproperty
        @override
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """
            return frozenset(("test_command_1",))

        @classproperty
        @override
        def ROLE_NAME(cls) -> str:
            """The name of the Discord role that does not exist."""
            return "role_name_1"

    def test_str_contains_formatted_message(self) -> None:
        """Test that the exception message contains the auto-generated formatted message."""
        assert self._RoleDoesNotExistErrorSubclass.get_formatted_message(
            non_existent_object_identifier=self._RoleDoesNotExistErrorSubclass.ROLE_NAME,
        ) in str(self._RoleDoesNotExistErrorSubclass())

    def test_role_name_in_str(self) -> None:
        """
        Test that the correct role name appears in the exception message.

        The correct channel name is the `ROLE_NAME` class-property
        associated with the given `RoleDoesNotExistError` subclass.
        """
        assert self._RoleDoesNotExistErrorSubclass.ROLE_NAME in str(
            self._RoleDoesNotExistErrorSubclass()
        )


class TestCommitteeRoleDoesNotExistError:
    """
    Test case to unit-test the `CommitteeRoleDoesNotExistError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `CommitteeRoleDoesNotExistError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestGuestRoleDoesNotExistError:
    """
    Test case to unit-test the `GuestRoleDoesNotExistError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `GuestRoleDoesNotExistError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestMemberRoleDoesNotExistError:
    """
    Test case to unit-test the `MemberRoleDoesNotExistError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `MemberRoleDoesNotExistError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestArchivistRoleDoesNotExistError:
    """
    Test case to unit-test the `ArchivistRoleDoesNotExistError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `ArchivistRoleDoesNotExistError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestChannelDoesNotExistError:
    """Test case to unit-test the `ChannelDoesNotExistError` exception."""

    class _ChannelDoesNotExistErrorSubclass(ChannelDoesNotExistError):  # noqa: N818
        """Custom subclass implementation of `ChannelDoesNotExistError`, for testing."""

        @classproperty
        @override
        def ERROR_CODE(cls) -> str:
            """The unique error code for users to tell admins about an error that occurred."""
            return "E1"

        @classproperty
        @override
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """
            return frozenset(("test_command_1",))

        @classproperty
        @override
        def CHANNEL_NAME(cls) -> str:
            """The name of the Discord channel that does not exist."""
            return "channel_name_1"

    def test_str_contains_formatted_message(self) -> None:
        """Test that the exception message contains the auto-generated formatted message."""
        assert self._ChannelDoesNotExistErrorSubclass.get_formatted_message(
            non_existent_object_identifier=self._ChannelDoesNotExistErrorSubclass.CHANNEL_NAME,
        ) in str(self._ChannelDoesNotExistErrorSubclass())

    def test_channel_name_in_str(self) -> None:
        """
        Test that the correct channel name appears in the exception message.

        The correct channel name is the `CHANNEL_NAME` class-property
        associated with the given `ChannelDoesNotExistError` subclass.
        """
        assert self._ChannelDoesNotExistErrorSubclass.CHANNEL_NAME in str(
            self._ChannelDoesNotExistErrorSubclass()
        )


class TestRolesChannelDoesNotExistError:
    """
    Test case to unit-test the `RolesChannelDoesNotExistError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `RolesChannelDoesNotExistError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """


class TestGeneralChannelDoesNotExistError:
    """
    Test case to unit-test the `GeneralChannelDoesNotExistError` exception.

    If there are no unit-tests within this test case,
    it is because all the functionality of `GeneralChannelDoesNotExistError` is inherited
    from its parent class so is already unit-tested in the parent class's dedicated test case.
    """
