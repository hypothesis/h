from copy import deepcopy

import pytest

from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.schema import Schema


def get_schema_example(schema_path):
    return deepcopy(Schema.get_schema(schema_path)["examples"][0])


@pytest.fixture
def group_command(group_attributes):
    return CommandBuilder.group.upsert(group_attributes, "id_ref")


@pytest.fixture
def user_command(user_attributes):
    return CommandBuilder.user.upsert("acct:user@example.com", user_attributes)


@pytest.fixture
def configuration_body():
    return get_schema_example("bulk_api/command/configuration.json")


@pytest.fixture
def upsert_user_body():
    return get_schema_example("bulk_api/command/upsert_user.json")


@pytest.fixture
def upsert_group_body():
    return get_schema_example("bulk_api/command/upsert_group.json")


@pytest.fixture
def create_group_membership_body():
    return get_schema_example("bulk_api/command/create_group_membership.json")


@pytest.fixture
def user_attributes(upsert_user_body):
    return upsert_user_body["data"]["attributes"]


@pytest.fixture
def group_attributes():
    return {"name": "name", "groupid": "group:name@example.com"}
