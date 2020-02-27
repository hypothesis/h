import pytest

from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)


class TestCommandBuilderFromData:
    def test_deserialise_user_ok(self, upsert_user_body):
        command = CommandBuilder.from_data(["upsert", upsert_user_body])

        assert isinstance(command.body, UpsertUser)

    def test_deserialise_user_can_fail(self, upsert_user_body):
        del upsert_user_body["data"]["id"]

        with pytest.raises(Exception):
            CommandBuilder.from_data(["upsert", upsert_user_body])

    def test_deserialise_group_ok(self, upsert_group_body):
        command = CommandBuilder.from_data(["upsert", upsert_group_body])

        assert isinstance(command.body, UpsertGroup)

    def test_deserialise_group_can_fail(self, upsert_group_body):
        del upsert_group_body["data"]["attributes"]["name"]

        with pytest.raises(Exception):
            CommandBuilder.from_data(["upsert", upsert_group_body])

    def test_deserialise_group_membership_ok(self, create_group_membership_body):
        command = CommandBuilder.from_data(["create", create_group_membership_body])

        assert isinstance(command.body, CreateGroupMembership)

    def test_deserialise_group_membership_can_fail(self, create_group_membership_body):
        del create_group_membership_body["data"]["relationships"]["group"]

        with pytest.raises(Exception):
            CommandBuilder.from_data(["create", create_group_membership_body])

    def test_deserialise_configure_ok(self, configure_object):
        raise NotImplementedError()


class TestCommandBuilderCreation:
    def test_at_all(self):
        raise NotImplementedError()
