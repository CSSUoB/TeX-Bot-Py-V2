"""Automated test suite for all custom exceptions within `exceptions.py`."""

from typing import TYPE_CHECKING, Final

import pytest
from classproperties import classproperty

from exceptions import (
    BaseDoesNotExistError,
    BaseTeXBotError,
    ChannelDoesNotExistError,
    DiscordMemberNotInMainGuildError,
    GuildDoesNotExistError,
    ImproperlyConfiguredError,
    InvalidMessagesJSONFileError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
    RoleDoesNotExistError,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


class TestImproperlyConfiguredError:
    """Test case to unit-test the `ImproperlyConfiguredError` exception."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_EXCEPTION_MESSAGE", ("Error 1 occurred",))
    def test_message(self, TEST_EXCEPTION_MESSAGE: str) -> None:  # noqa: N803
        """Test that the custom error message is used in the `__str__` representation."""
        assert str(ImproperlyConfiguredError(TEST_EXCEPTION_MESSAGE)) == TEST_EXCEPTION_MESSAGE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_EXCEPTION_MESSAGE", ("Error 1 occurred",))
    def test_message_when_raised(self, TEST_EXCEPTION_MESSAGE: str) -> None:  # noqa: N803
        """Test that the custom error message is shown when the exception is raised."""
        with pytest.raises(ImproperlyConfiguredError, match=TEST_EXCEPTION_MESSAGE):
            raise ImproperlyConfiguredError(TEST_EXCEPTION_MESSAGE)


class TestBaseTeXBotError:
    """Test case to unit-test the `BaseTeXBotError` exception."""

    class _DefaultMessageBaseTeXBotErrorSubclass(BaseTeXBotError):
        """
        Custom subclass implementation of `BaseTeXBotError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has a `DEFAULT_MESSAGE` set.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
            """The message to be displayed alongside this exception class if not provided."""  # noqa: D401
            return "Error 1 occurred"

    class _AttributesBaseTeXBotErrorSubclass(_DefaultMessageBaseTeXBotErrorSubclass):
        """
        Custom subclass implementation of `BaseTeXBotError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has a new instance attribute (compared to the parent base class).
        """

        def __init__(self, message: str | None = None, test_attribute_value: object | None = None) -> None:  # noqa: E501
            """Initialize a new exception with the given error message."""
            self.test_attribute: object | None = test_attribute_value

            super().__init__(message=message)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_BASE_TEXBOT_ERROR_SUBCLASS",
        (
            _DefaultMessageBaseTeXBotErrorSubclass(),
            _DefaultMessageBaseTeXBotErrorSubclass(message=None),
            _DefaultMessageBaseTeXBotErrorSubclass(message="")
        )
    )
    def test_default_message(self, TEST_BASE_TEXBOT_ERROR_SUBCLASS: BaseTeXBotError) -> None:  # noqa: N803
        """Test that the class' default error message is shown, when no custom message."""
        assert (
            TEST_BASE_TEXBOT_ERROR_SUBCLASS.message
            == self._DefaultMessageBaseTeXBotErrorSubclass.DEFAULT_MESSAGE
        )
        assert (
            str(TEST_BASE_TEXBOT_ERROR_SUBCLASS)
            == self._DefaultMessageBaseTeXBotErrorSubclass.DEFAULT_MESSAGE
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_EXCEPTION_MESSAGE", ("Other test error occurred",))
    def test_custom_message(self, TEST_EXCEPTION_MESSAGE: str) -> None:  # noqa: N803
        """Test that the custom error message is shown, when given."""
        assert (
            self._DefaultMessageBaseTeXBotErrorSubclass(TEST_EXCEPTION_MESSAGE).message
            == TEST_EXCEPTION_MESSAGE
        )
        assert (
            str(self._DefaultMessageBaseTeXBotErrorSubclass(TEST_EXCEPTION_MESSAGE))
            == TEST_EXCEPTION_MESSAGE
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_ATTRIBUTES_BASE_TEXBOT_ERROR_SUBCLASS",
        (
            _AttributesBaseTeXBotErrorSubclass(),
            _AttributesBaseTeXBotErrorSubclass(test_attribute_value=None),
            _AttributesBaseTeXBotErrorSubclass(test_attribute_value=7)
        )
    )
    def test_repr_with_attributes(self, TEST_ATTRIBUTES_BASE_TEXBOT_ERROR_SUBCLASS: _AttributesBaseTeXBotErrorSubclass) -> None:  # noqa: N803,E501
        """Test that the exception message contains any instance attributes."""
        assert (
            f"test_attribute={TEST_ATTRIBUTES_BASE_TEXBOT_ERROR_SUBCLASS.test_attribute!r}"
            in repr(TEST_ATTRIBUTES_BASE_TEXBOT_ERROR_SUBCLASS)
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

    class _NoDependantsBaseDoesNotExistErrorSubclass(BaseDoesNotExistError):
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has no dependent commands, tasks or events.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
            """The message to be displayed alongside this exception class if not provided."""  # noqa: D401
            return "Error 1 occurred"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ERROR_CODE(cls) -> str:  # noqa: N802,N805
            """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
            return "E1"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DOES_NOT_EXIST_TYPE(cls) -> str:  # noqa: N802,N805
            """The name of the Discord entity that this `DoesNotExistError` is attached to."""  # noqa: D401
            return "object_type"

    class _OneDependentCommandBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):  # noqa: E501
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has one command dependent.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """  # noqa: D401
            return frozenset(("command_1",))

    class _MultipleDependentCommandsBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):  # noqa: E501
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has multiple dependent commands.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """  # noqa: D401
            return frozenset(("command_1", "command_2", "command_3"))

    class _OneDependentTaskBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):  # noqa: E501
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has one task dependent.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_TASKS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot tasks that require this Discord entity.

            This set being empty could mean that all bot tasks require this Discord entity,
            or no bot tasks require this Discord entity.
            """  # noqa: D401
            return frozenset(("task_1",))

    class _MultipleDependentTasksBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):  # noqa: E501
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has multiple dependent tasks.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_TASKS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot tasks that require this Discord entity.

            This set being empty could mean that all bot tasks require this Discord entity,
            or no bot tasks require this Discord entity.
            """  # noqa: D401
            return frozenset(("task_1", "task_2", "task_3"))

    class _OneDependentEventBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):  # noqa: E501
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has one event dependent.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_EVENTS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot events that require this Discord entity.

            This set being empty could mean that all bot events require this Discord entity,
            or no bot events require this Discord entity.
            """  # noqa: D401
            return frozenset(("event_1",))

    class _MultipleDependentEventsBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):  # noqa: E501
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass that has multiple dependent events.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_EVENTS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot events that require this Discord entity.

            This set being empty could mean that all bot events require this Discord entity,
            or no bot events require this Discord entity.
            """  # noqa: D401
            return frozenset(("event_1", "event_2", "event_3"))

    class _ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):  # noqa: E501
        """
        Custom subclass implementation of `BaseDoesNotExistError`.

        This specific custom subclass implementation is used for testing
        with a subclass whose `DOES_NOT_EXIST_TYPE` is a channel.
        """

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """  # noqa: D401
            return frozenset(("command_1",))

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DOES_NOT_EXIST_TYPE(cls) -> str:  # noqa: N802,N805
            """The name of the Discord entity that this `DoesNotExistError` is attached to."""  # noqa: D401
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
                non_existent_object_identifier="object_1"
            )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "DependentCommandsBaseDoesNotExistErrorSubclass",
        (
            _OneDependentCommandBaseDoesNotExistErrorSubclass,
            _MultipleDependentCommandsBaseDoesNotExistErrorSubclass
        )
    )
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_dependent_commands(self, DependentCommandsBaseDoesNotExistErrorSubclass: type[_NoDependantsBaseDoesNotExistErrorSubclass], TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:  # noqa: N803,E501
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        that has either one, or multiple dependent commands.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the list of dependent command names separated by "," (comma) characters.
        """
        FORMATTED_MESSAGE: Final[str] = (
            DependentCommandsBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
        )

        assert (
            (
                f"\"{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"{DependentCommandsBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE} "
                f"must exist"
            )
            in FORMATTED_MESSAGE
        )

        if len(DependentCommandsBaseDoesNotExistErrorSubclass.DEPENDENT_COMMANDS) == 1:
            assert (
                (
                    "the "
                    f"""\"/{
                        next(
                            iter(
                                DependentCommandsBaseDoesNotExistErrorSubclass.DEPENDENT_COMMANDS
                            )
                        )
                    }\" """
                    "command"
                )
                in FORMATTED_MESSAGE
            )

        elif len(DependentCommandsBaseDoesNotExistErrorSubclass.DEPENDENT_COMMANDS) > 1:
            DEPENDENT_COMMANDS: Final[Iterator[str]] = iter(
                DependentCommandsBaseDoesNotExistErrorSubclass.DEPENDENT_COMMANDS
            )

            assert (
                (
                    f"the \"/{next(DEPENDENT_COMMANDS)}\", \"/{next(DEPENDENT_COMMANDS)}\" & "
                    f"\"/{next(DEPENDENT_COMMANDS)}\" commands"
                )
                in FORMATTED_MESSAGE
            )

        else:
            raise NotImplementedError

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "DependentTasksBaseDoesNotExistErrorSubclass",
        (
            _OneDependentTaskBaseDoesNotExistErrorSubclass,
            _MultipleDependentTasksBaseDoesNotExistErrorSubclass
        )
    )
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_dependent_tasks(self, DependentTasksBaseDoesNotExistErrorSubclass: type[_NoDependantsBaseDoesNotExistErrorSubclass], TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:  # noqa: N803,E501
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        that has either one, or multiple dependent tasks.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the list of dependent task names separated by "," (comma) characters.
        """
        FORMATTED_MESSAGE: Final[str] = (
            DependentTasksBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
        )

        assert (
            (
                f"\"{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"{DependentTasksBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE} "
                f"must exist"
            )
            in FORMATTED_MESSAGE
        )

        if len(DependentTasksBaseDoesNotExistErrorSubclass.DEPENDENT_TASKS) == 1:
            assert (
                (
                    "the "
                    f"""\"{
                        next(iter(DependentTasksBaseDoesNotExistErrorSubclass.DEPENDENT_TASKS))
                    }\" """
                    "task"
                )
                in FORMATTED_MESSAGE
            )

        elif len(DependentTasksBaseDoesNotExistErrorSubclass.DEPENDENT_TASKS) > 1:
            DEPENDENT_TASKS: Final[Iterator[str]] = iter(
                DependentTasksBaseDoesNotExistErrorSubclass.DEPENDENT_TASKS
            )

            assert (
                (
                    f"the \"{next(DEPENDENT_TASKS)}\", \"{next(DEPENDENT_TASKS)}\" & "
                    f"\"{next(DEPENDENT_TASKS)}\" tasks"
                )
                in FORMATTED_MESSAGE
            )

        else:
            raise NotImplementedError

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "DependentEventsBaseDoesNotExistErrorSubclass",
        (
            _OneDependentEventBaseDoesNotExistErrorSubclass,
            _MultipleDependentEventsBaseDoesNotExistErrorSubclass
        )
    )
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_dependent_events(self, DependentEventsBaseDoesNotExistErrorSubclass: type[_NoDependantsBaseDoesNotExistErrorSubclass], TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:  # noqa: N803,E501
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        that has either one, or multiple dependent events.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the list of dependent event names separated by "," (comma) characters.
        """
        FORMATTED_MESSAGE: Final[str] = (
            DependentEventsBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
        )

        assert (
            (
                f"\"{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"{DependentEventsBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE} "
                f"must exist"
            )
            in FORMATTED_MESSAGE
        )

        if len(DependentEventsBaseDoesNotExistErrorSubclass.DEPENDENT_EVENTS) == 1:
            assert (
                (
                    "the "
                    f"""\"{
                        next(
                            iter(DependentEventsBaseDoesNotExistErrorSubclass.DEPENDENT_EVENTS)
                        )
                    }\" """
                    "event"
                )
                in FORMATTED_MESSAGE
            )

        elif len(DependentEventsBaseDoesNotExistErrorSubclass.DEPENDENT_EVENTS) > 1:
            DEPENDENT_EVENTS: Final[Iterator[str]] = iter(
                DependentEventsBaseDoesNotExistErrorSubclass.DEPENDENT_EVENTS
            )

            assert (
                (
                    f"the \"{next(DEPENDENT_EVENTS)}\", \"{next(DEPENDENT_EVENTS)}\" & "
                    f"\"{next(DEPENDENT_EVENTS)}\" events"
                )
                in FORMATTED_MESSAGE
            )

        else:
            raise NotImplementedError

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_channel_does_not_exist_type(self, TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:  # noqa: N803,E501
        """
        Test that the `get_formatted_message()` function returns the correct value.

        This test is run with a `BaseDoesNotExistError` subclass
        whose `DOES_NOT_EXIST_TYPE` is a Discord channel.
        In this case, the correct return value of the `get_formatted_message()` function
        should contain the Discord channel name prefixed by a "#" (hashtag) character,
        as well as the word "channel".
        """
        assert (
            (
                f"\"#{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"""{
                    self._ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE
                } """
                "must exist"
            )
            in self._ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass.get_formatted_message(  # noqa: E501
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
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

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_USER_ID", (99999,))
    def test_user_id_in_repr(self, TEST_USER_ID: int) -> None:  # noqa: N803
        """Test that the exception message contains the given Discord user ID."""
        assert (
            f"user_id={TEST_USER_ID!r}"
            in repr(DiscordMemberNotInMainGuildError(user_id=TEST_USER_ID))
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

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_DICT_KEY", ("key_1",))
    def test_dict_key_in_repr(self, TEST_DICT_KEY: str) -> None:  # noqa: N803
        """Test that the exception message contains the given dict key."""
        assert (
            f"dict_key={TEST_DICT_KEY!r}"
            in repr(InvalidMessagesJSONFileError(dict_key=TEST_DICT_KEY))
        )


class TestMessagesJSONFileMissingKeyError:
    """Test case to unit-test the `MessagesJSONFileMissingKeyError` exception."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MISSING_KEY", ("key_1",))
    def test_missing_key_in_repr(self, TEST_MISSING_KEY: str) -> None:  # noqa: N803
        """Test that the exception message contains the given JSON file missing key name."""
        assert (
            f"dict_key={TEST_MISSING_KEY!r}"
            in repr(MessagesJSONFileMissingKeyError(missing_key=TEST_MISSING_KEY))
        )


class TestMessagesJSONFileValueError:
    """Test case to unit-test the `MessagesJSONFileValueError` exception."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_JSON_FILE_INVALID_VALUE", ("value_1",))
    def test_invalid_value_in_repr(self, TEST_JSON_FILE_INVALID_VALUE: str) -> None:  # noqa: N803
        """Test that the exception message contains the given invalid JSON file value."""
        assert (
            f"invalid_value={TEST_JSON_FILE_INVALID_VALUE!r}"
            in repr(MessagesJSONFileValueError(invalid_value=TEST_JSON_FILE_INVALID_VALUE))
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

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_GUILD_ID", (99999,))
    def test_guild_id_in_repr(self, TEST_GUILD_ID: int) -> None:  # noqa: N803
        """Test that the exception message contains the given Discord guild ID."""
        assert (
            f"guild_id={TEST_GUILD_ID!r}"
            in repr(GuildDoesNotExistError(guild_id=TEST_GUILD_ID))
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_GUILD_ID", (99999,))
    def test_default_message_with_guild_id(self, TEST_GUILD_ID: int) -> None:  # noqa: N803
        """
        Test that the exception message contains the default error message.

        This test instantiates the GuildDoesNotExistError exception
        with a specific Discord guild ID,
        so the default error message should also contain the given Discord guild ID.
        """
        assert (
            f"ID \"{TEST_GUILD_ID}\"" in str(GuildDoesNotExistError(guild_id=TEST_GUILD_ID))
        )

    def test_default_message_without_guild_id(self) -> None:
        """
        Test that the exception message contains the default error message.

        This test instantiates the GuildDoesNotExistError exception
        without a specific Discord guild ID,
        so the default error message should just contain "given ID".
        """
        assert "given ID" in str(GuildDoesNotExistError())


class TestRoleDoesNotExistError:
    """Test case to unit-test the `RoleDoesNotExistError` exception."""

    class _RoleDoesNotExistErrorSubclass(RoleDoesNotExistError):
        """Custom subclass implementation of `RoleDoesNotExistError`, for testing purposes."""

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ERROR_CODE(cls) -> str:  # noqa: N802,N805
            """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
            return "E1"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """  # noqa: D401
            return frozenset(("test_command_1",))

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ROLE_NAME(cls) -> str:  # noqa: N802,N805
            """The name of the Discord role that does not exist."""  # noqa: D401
            return "role_name_1"

    def test_str_contains_formatted_message(self) -> None:
        """Test that the exception message contains the auto-generated formatted message."""
        assert (
            self._RoleDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=self._RoleDoesNotExistErrorSubclass.ROLE_NAME
            )
            in str(self._RoleDoesNotExistErrorSubclass())
        )

    def test_role_name_in_str(self) -> None:
        """
        Test that the correct role name appears in the exception message.

        The correct channel name is the `ROLE_NAME` class-property
        associated with the given `RoleDoesNotExistError` subclass.
        """
        assert (
            self._RoleDoesNotExistErrorSubclass.ROLE_NAME
            in str(self._RoleDoesNotExistErrorSubclass())
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

    class _ChannelDoesNotExistErrorSubclass(ChannelDoesNotExistError):
        """Custom subclass implementation of `ChannelDoesNotExistError`, for testing."""

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ERROR_CODE(cls) -> str:  # noqa: N802,N805
            """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401
            return "E1"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
            """
            The set of names of bot commands that require this Discord entity.

            This set being empty could mean that all bot commands require this Discord entity,
            or no bot commands require this Discord entity.
            """  # noqa: D401
            return frozenset(("test_command_1",))

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def CHANNEL_NAME(cls) -> str:  # noqa: N802,N805
            """The name of the Discord channel that does not exist."""  # noqa: D401
            return "channel_name_1"

    def test_str_contains_formatted_message(self) -> None:
        """Test that the exception message contains the auto-generated formatted message."""
        assert (
            self._ChannelDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=self._ChannelDoesNotExistErrorSubclass.CHANNEL_NAME
            )
            in str(self._ChannelDoesNotExistErrorSubclass())
        )

    def test_channel_name_in_str(self) -> None:
        """
        Test that the correct channel name appears in the exception message.

        The correct channel name is the `CHANNEL_NAME` class-property
        associated with the given `ChannelDoesNotExistError` subclass.
        """
        assert (
            self._ChannelDoesNotExistErrorSubclass.CHANNEL_NAME
            in str(self._ChannelDoesNotExistErrorSubclass())
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
