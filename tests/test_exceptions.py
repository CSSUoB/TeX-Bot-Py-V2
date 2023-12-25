from collections.abc import Iterator
from typing import Final

import pytest
from classproperties import classproperty

from exceptions import BaseDoesNotExistError, BaseTeXBotError, ImproperlyConfiguredError, UserNotInCSSDiscordServerError, InvalidMessagesJSONFileError, MessagesJSONFileMissingKeyError, MessagesJSONFileValueError, GuildDoesNotExistError, RoleDoesNotExistError, ChannelDoesNotExistError


class TestImproperlyConfiguredError:
    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_EXCEPTION_MESSAGE", ("Error 1 occurred",))
    def test_message(self, TEST_EXCEPTION_MESSAGE: str) -> None:
        assert str(ImproperlyConfiguredError(TEST_EXCEPTION_MESSAGE)) == TEST_EXCEPTION_MESSAGE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_EXCEPTION_MESSAGE", ("Error 1 occurred",))
    def test_message_when_raised(self, TEST_EXCEPTION_MESSAGE: str) -> None:
        with pytest.raises(ImproperlyConfiguredError, match=TEST_EXCEPTION_MESSAGE):
            raise ImproperlyConfiguredError(TEST_EXCEPTION_MESSAGE)


class TestBaseTeXBotError:
    class _DefaultMessageBaseTeXBotErrorSubclass(BaseTeXBotError):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
            return "Error 1 occurred"

    class _AttributesBaseTeXBotErrorSubclass(_DefaultMessageBaseTeXBotErrorSubclass):
        def __init__(self, message: str | None = None, test_attribute_value: object | None = None) -> None:
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
    def test_default_message(self, TEST_BASE_TEXBOT_ERROR_SUBCLASS: BaseTeXBotError) -> None:
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
    def test_custom_message(self, TEST_EXCEPTION_MESSAGE: str) -> None:
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
    def test_repr_with_attributes(self, TEST_ATTRIBUTES_BASE_TEXBOT_ERROR_SUBCLASS: _AttributesBaseTeXBotErrorSubclass) -> None:
        assert (
            f"test_attribute={TEST_ATTRIBUTES_BASE_TEXBOT_ERROR_SUBCLASS.test_attribute!r}"
            in repr(TEST_ATTRIBUTES_BASE_TEXBOT_ERROR_SUBCLASS)
        )


class TestBaseErrorWithErrorCode:
    """"""


class TestBaseDoesNotExistError:
    class _NoDependantsBaseDoesNotExistErrorSubclass(BaseDoesNotExistError):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
            return "Error 1 occurred"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ERROR_CODE(self) -> str:  # noqa: N805,N802
            return "E1"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DOES_NOT_EXIST_TYPE(self) -> str:  # noqa: N805,N802
            return "object_type"

    class _OneDependantCommandBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("command_1",))

    class _MultipleDependantCommandsBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("command_1", "command_2", "command_3"))

    class _OneDependantTaskBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_TASKS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("task_1",))

    class _MultipleDependantTasksBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_TASKS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("task_1", "task_2", "task_3"))

    class _OneDependantEventBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_EVENTS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("event_1",))

    class _MultipleDependantEventsBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_EVENTS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("event_1", "event_2", "event_3"))

    class _ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass(_NoDependantsBaseDoesNotExistErrorSubclass):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("command_1",))

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DOES_NOT_EXIST_TYPE(self) -> str:  # noqa: N805,N802
            return "channel"

    def test_get_formatted_message_with_no_dependants(self) -> None:
        with pytest.raises(ValueError, match="no dependants"):
            self._NoDependantsBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier="object_1"
            )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "DependantCommandsBaseDoesNotExistErrorSubclass",
        (
            _OneDependantCommandBaseDoesNotExistErrorSubclass,
            _MultipleDependantCommandsBaseDoesNotExistErrorSubclass
        )
    )
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_dependant_commands(self, DependantCommandsBaseDoesNotExistErrorSubclass: type[_NoDependantsBaseDoesNotExistErrorSubclass], TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:
        FORMATTED_MESSAGE: Final[str] = (
            DependantCommandsBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
        )

        assert (
            (
                f"\"{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"{DependantCommandsBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE} "
                f"must exist"
            )
            in FORMATTED_MESSAGE
        )

        if len(DependantCommandsBaseDoesNotExistErrorSubclass.DEPENDANT_COMMANDS) == 1:
            assert (
                (
                    "the "
                    f"""\"/{
                        next(
                            iter(
                                DependantCommandsBaseDoesNotExistErrorSubclass.DEPENDANT_COMMANDS
                            )
                        )
                    }\" """
                    "command"
                )
                in FORMATTED_MESSAGE
            )

        elif len(DependantCommandsBaseDoesNotExistErrorSubclass.DEPENDANT_COMMANDS) > 1:
            DEPENDANT_COMMANDS: Final[Iterator[str]] = iter(
                DependantCommandsBaseDoesNotExistErrorSubclass.DEPENDANT_COMMANDS
            )

            assert (
                (
                    f"the \"/{next(DEPENDANT_COMMANDS)}\", \"/{next(DEPENDANT_COMMANDS)}\" & "
                    f"\"/{next(DEPENDANT_COMMANDS)}\" commands"
                )
                in FORMATTED_MESSAGE
            )

        else:
            raise NotImplementedError

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "DependantTasksBaseDoesNotExistErrorSubclass",
        (
            _OneDependantTaskBaseDoesNotExistErrorSubclass,
            _MultipleDependantTasksBaseDoesNotExistErrorSubclass
        )
    )
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_dependant_tasks(self, DependantTasksBaseDoesNotExistErrorSubclass: type[_NoDependantsBaseDoesNotExistErrorSubclass], TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:
        FORMATTED_MESSAGE: Final[str] = (
            DependantTasksBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
        )

        assert (
            (
                f"\"{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"{DependantTasksBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE} "
                f"must exist"
            )
            in FORMATTED_MESSAGE
        )

        if len(DependantTasksBaseDoesNotExistErrorSubclass.DEPENDANT_TASKS) == 1:
            assert (
                (
                    "the "
                    f"""\"{
                        next(iter(DependantTasksBaseDoesNotExistErrorSubclass.DEPENDANT_TASKS))
                    }\" """
                    "task"
                )
                in FORMATTED_MESSAGE
            )

        elif len(DependantTasksBaseDoesNotExistErrorSubclass.DEPENDANT_TASKS) > 1:
            DEPENDANT_TASKS: Final[Iterator[str]] = iter(
                DependantTasksBaseDoesNotExistErrorSubclass.DEPENDANT_TASKS
            )

            assert (
                (
                    f"the \"{next(DEPENDANT_TASKS)}\", \"{next(DEPENDANT_TASKS)}\" & "
                    f"\"{next(DEPENDANT_TASKS)}\" tasks"
                )
                in FORMATTED_MESSAGE
            )

        else:
            raise NotImplementedError

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "DependantEventsBaseDoesNotExistErrorSubclass",
        (
            _OneDependantEventBaseDoesNotExistErrorSubclass,
            _MultipleDependantEventsBaseDoesNotExistErrorSubclass
        )
    )
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_dependant_tasks(self, DependantEventsBaseDoesNotExistErrorSubclass: type[_NoDependantsBaseDoesNotExistErrorSubclass], TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:
        FORMATTED_MESSAGE: Final[str] = (
            DependantEventsBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
        )

        assert (
            (
                f"\"{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"{DependantEventsBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE} "
                f"must exist"
            )
            in FORMATTED_MESSAGE
        )

        if len(DependantEventsBaseDoesNotExistErrorSubclass.DEPENDANT_EVENTS) == 1:
            assert (
                (
                    "the "
                    f"""\"{
                        next(
                            iter(DependantEventsBaseDoesNotExistErrorSubclass.DEPENDANT_EVENTS)
                        )
                    }\" """
                    "event"
                )
                in FORMATTED_MESSAGE
            )

        elif len(DependantEventsBaseDoesNotExistErrorSubclass.DEPENDANT_EVENTS) > 1:
            DEPENDANT_EVENTS: Final[Iterator[str]] = iter(
                DependantEventsBaseDoesNotExistErrorSubclass.DEPENDANT_EVENTS
            )

            assert (
                (
                    f"the \"{next(DEPENDANT_EVENTS)}\", \"{next(DEPENDANT_EVENTS)}\" & "
                    f"\"{next(DEPENDANT_EVENTS)}\" events"
                )
                in FORMATTED_MESSAGE
            )

        else:
            raise NotImplementedError

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_NON_EXISTENT_OBJECT_IDENTIFIER", ("object_1",))
    def test_get_formatted_message_with_channel_does_not_exist_type(self, TEST_NON_EXISTENT_OBJECT_IDENTIFIER: str) -> None:
        assert (
            (
                f"\"#{TEST_NON_EXISTENT_OBJECT_IDENTIFIER}\" "
                f"""{
                    self._ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass.DOES_NOT_EXIST_TYPE
                } """
                "must exist"
            )
            in self._ChannelDoesNotExistTypeBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=TEST_NON_EXISTENT_OBJECT_IDENTIFIER
            )
        )


class TestRulesChannelDoesNotExist:
    """"""


class TestUserNotInCSSDiscordServerError:
    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_USER_ID", (99999,))
    def test_user_id_in_repr(self, TEST_USER_ID: int) -> None:
        assert (
            f"user_id={TEST_USER_ID!r}"
            in repr(UserNotInCSSDiscordServerError(user_id=TEST_USER_ID))
        )


class TestEveryoneRoleCouldNotBeRetrievedError:
    """"""


class TestInvalidMessagesJSONFileError:
    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_DICT_KEY", ("key_1",))
    def test_dict_key_in_repr(self, TEST_DICT_KEY: str) -> None:
        assert (
            f"dict_key={TEST_DICT_KEY!r}"
            in repr(InvalidMessagesJSONFileError(dict_key=TEST_DICT_KEY))
        )


class TestMessagesJSONFileMissingKeyError:
    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MISSING_KEY", ("key_1",))
    def test_missing_key_in_repr(self, TEST_MISSING_KEY: str) -> None:
        assert (
            f"dict_key={TEST_MISSING_KEY!r}"
            in repr(MessagesJSONFileMissingKeyError(missing_key=TEST_MISSING_KEY))
        )


class TestMessagesJSONFileValueError:
    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_JSON_FILE_INVALID_VALUE", ("value_1",))
    def test_invalid_value_in_repr(self, TEST_JSON_FILE_INVALID_VALUE: str) -> None:
        assert (
            f"invalid_value={TEST_JSON_FILE_INVALID_VALUE!r}"
            in repr(MessagesJSONFileValueError(invalid_value=TEST_JSON_FILE_INVALID_VALUE))
        )


class TestStrikeTrackingError:
    """"""


class TestGuildDoesNotExistError:
    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_GUILD_ID", (99999,))
    def test_guild_id_in_repr(self, TEST_GUILD_ID: int) -> None:
        assert (
            f"guild_id={TEST_GUILD_ID!r}"
            in repr(GuildDoesNotExistError(guild_id=TEST_GUILD_ID))
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_GUILD_ID", (99999,))
    def test_default_message_with_guild_id(self, TEST_GUILD_ID: int) -> None:
        assert (
            f"ID \"{TEST_GUILD_ID}\"" in repr(GuildDoesNotExistError(guild_id=TEST_GUILD_ID))
        )

    def test_default_message_without_guild_id(self) -> None:
        assert "given ID" in repr(GuildDoesNotExistError())


class TestRoleDoesNotExistError:
    class _RoleDoesNotExistErrorSubclass(RoleDoesNotExistError):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ERROR_CODE(self) -> str:  # noqa: N805,N802
            return "E1"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("test_command_1",))

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ROLE_NAME(self) -> str:  # noqa: N805,N802
            return "role_name_1"

    def test_formatted_message_in_repr(self) -> None:
        assert (
            self._RoleDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=self._RoleDoesNotExistErrorSubclass.ROLE_NAME
            )
            in repr(self._RoleDoesNotExistErrorSubclass())
        )

    def test_role_name_in_repr(self) -> None:
        assert (
            self._RoleDoesNotExistErrorSubclass.ROLE_NAME
            in repr(self._RoleDoesNotExistErrorSubclass())
        )


class TestCommitteeRoleDoesNotExistError:
    """"""


class TestGuestRoleDoesNotExistError:
    """"""


class TestMemberRoleDoesNotExistError:
    """"""


class TestArchivistRoleDoesNotExistError:
    """"""


class TestChannelDoesNotExistError:
    class _ChannelDoesNotExistErrorSubclass(ChannelDoesNotExistError):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ERROR_CODE(self) -> str:  # noqa: N805,N802
            return "E1"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEPENDANT_COMMANDS(self) -> frozenset[str]:  # noqa: N805,N802
            return frozenset(("test_command_1",))

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def CHANNEL_NAME(self) -> str:  # noqa: N805,N802
            return "channel_name_1"

    def test_formatted_message_in_repr(self) -> None:
        assert (
            self._ChannelDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier=self._ChannelDoesNotExistErrorSubclass.CHANNEL_NAME
            )
            in repr(self._ChannelDoesNotExistErrorSubclass())
        )

    def test_channel_name_in_repr(self) -> None:
        assert (
            self._ChannelDoesNotExistErrorSubclass.CHANNEL_NAME
            in repr(self._ChannelDoesNotExistErrorSubclass())
        )


class TestRolesChannelDoesNotExistError:
    """"""


class TestGeneralChannelDoesNotExistError:
    """"""
