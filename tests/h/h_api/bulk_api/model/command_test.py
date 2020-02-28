from unittest.mock import create_autospec

import pytest

from h.h_api.bulk_api.model.command import Command, ConfigCommand, DataCommand
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.bulk_api.model.data_body import UpsertUser
from h.h_api.enums import CommandType, DataType
from h.h_api.exceptions import SchemaValidationError
from h.h_api.model.base import Model


class TestCommand:
    def test_from_raw(self, upsert_user_body):
        command = Command([CommandType.CREATE.value, upsert_user_body])

        self._check_command(command, upsert_user_body)

    def test_create(self, upsert_user_body):
        command = Command.create(CommandType.CREATE, UpsertUser(upsert_user_body))

        self._check_command(command, upsert_user_body)

    @pytest.mark.parametrize(
        "raw",
        (
            {},
            ["wrong", {}],
            [CommandType.CREATE.value, {}],
            [CommandType.CONFIGURE.value, []],
        ),
    )
    def test_we_apply_validation(self, raw):
        with pytest.raises(SchemaValidationError):
            Command(raw)

    def test_if_body_is_a_model_we_apply_its_validation(self, model):
        class CommandWithModelBody(Command):
            validator = None
            body = model

        command = CommandWithModelBody(CommandType.UPSERT, {})

        try:
            command.validate()
        finally:
            model.validate.assert_called_once()

    def _check_command(self, command, body):
        isinstance(command, Command)

        assert command.type == CommandType.CREATE
        assert command.body == body

        assert command.raw == [CommandType.CREATE.value, body]

    @pytest.fixture
    def model(self, upsert_user_body):
        return create_autospec(Model, instance=True)


class TestConfigCommand:
    def test_from_raw(self, configuration_body):
        command = ConfigCommand([CommandType.CONFIGURE.value, configuration_body])

        self._check_command(command, configuration_body)

    def test_create(self, configuration_body):
        command = ConfigCommand.create(Configuration(configuration_body))

        self._check_command(command, configuration_body)

    def _check_command(self, command, body):
        isinstance(command, ConfigCommand)

        assert command.type == CommandType.CONFIGURE
        assert isinstance(command.body, Configuration)
        assert command.body.raw == body

        assert command.raw == [CommandType.CONFIGURE.value, body]


class TestDataCommand:
    def test_from_raw(self, UpsertUserCommand, upsert_user_body):
        command = UpsertUserCommand([CommandType.UPSERT.value, upsert_user_body])

        assert isinstance(command, UpsertUserCommand)
        assert isinstance(command.body, UpsertUser)

    def test_we_cannot_create_another_type(self, UpsertUserCommand, upsert_group_body):
        with pytest.raises(TypeError):
            UpsertUserCommand([CommandType.CREATE.value, upsert_group_body])

    @pytest.fixture
    def UpsertUserCommand(self):
        class UpsertUserCommand(DataCommand):
            data_classes = {DataType.USER: UpsertUser}

        return UpsertUserCommand
