import pytest

from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.bulk_api.model.command import ConfigCommand, CreateCommand, UpsertCommand
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)
from h.h_api.enums import CommandType
from h.h_api.exceptions import SchemaValidationError

UPSERT = CommandType.UPSERT.value
CREATE = CommandType.CREATE.value
CONFIGURE = CommandType.CONFIGURE.value


class TestCommandBuilderFromData:
    def test_deserialise_user_ok(self, upsert_user_body):
        command = CommandBuilder.from_data([UPSERT, upsert_user_body])

        assert isinstance(command.body, UpsertUser)

    def test_deserialise_user_can_fail(self, upsert_user_body):
        del upsert_user_body["data"]["id"]

        with pytest.raises(SchemaValidationError):
            CommandBuilder.from_data([UPSERT, upsert_user_body])

    def test_deserialise_group_ok(self, upsert_group_body):
        command = CommandBuilder.from_data([UPSERT, upsert_group_body])

        assert isinstance(command.body, UpsertGroup)

    def test_deserialise_group_can_fail(self, upsert_group_body):
        del upsert_group_body["data"]["attributes"]["name"]

        with pytest.raises(SchemaValidationError):
            CommandBuilder.from_data([UPSERT, upsert_group_body])

    def test_deserialise_group_membership_ok(self, create_group_membership_body):
        command = CommandBuilder.from_data([CREATE, create_group_membership_body])

        assert isinstance(command.body, CreateGroupMembership)

    def test_deserialise_group_membership_can_fail(self, create_group_membership_body):
        del create_group_membership_body["data"]["relationships"]["group"]

        with pytest.raises(SchemaValidationError):
            CommandBuilder.from_data([CREATE, create_group_membership_body])

    def test_deserialise_configure_ok(self, configuration_body):
        command = CommandBuilder.from_data([CONFIGURE, configuration_body])

        assert isinstance(command.body, Configuration)

    def test_deserialise_configure_can_fail(self, configuration_body):
        configuration_body["random"] = "new_value"

        with pytest.raises(SchemaValidationError):
            CommandBuilder.from_data([CONFIGURE, configuration_body])


class TestCommandBuilderCreation:
    def test_configure(self):
        command = CommandBuilder.configure("acct:user@example.com", 2)

        assert isinstance(command, ConfigCommand)
        assert isinstance(command.body, Configuration)
        assert command.body.effective_user == "acct:user@example.com"
        assert command.body.total_instructions == 2

    def test_user_upsert(self, user_attributes):
        command = CommandBuilder.user.upsert("acct:user@example.com", user_attributes)

        assert isinstance(command, UpsertCommand)
        assert isinstance(command.body, UpsertUser)
        assert command.body.id == "acct:user@example.com"
        assert command.body.attributes == user_attributes

    def test_group_upsert(self, group_attributes):
        command = CommandBuilder.group.upsert(group_attributes, "id_ref")

        assert isinstance(command, UpsertCommand)
        assert isinstance(command.body, UpsertGroup)
        assert command.body.id_reference == "id_ref"
        assert command.body.attributes == group_attributes

    def test_group_membership_create(self):
        command = CommandBuilder.group_membership.create(
            "acct:user@example.com", "id_ref"
        )

        assert isinstance(command, CreateCommand)
        assert isinstance(command.body, CreateGroupMembership)
        assert command.body.member_id == "acct:user@example.com"
        assert command.body.group_ref == "id_ref"
