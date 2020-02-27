from copy import deepcopy

import pytest

from h.h_api.schema import Schema


def get_schema_example(schema_path):
    return deepcopy(Schema.get_schema(schema_path)["examples"][0])


@pytest.fixture
def user_attributes(upsert_user_object):
    return upsert_user_object["data"]["attributes"]


@pytest.fixture
def upsert_user_object():
    return get_schema_example("bulk_api/command/upsert_user.json")


@pytest.fixture
def group_attributes():
    return {"name": "name", "groupid": "group:name@example.com"}


@pytest.fixture
def upsert_group_body():
    return get_schema_example("bulk_api/command/upsert_group.json")


@pytest.fixture
def create_group_membership_object():
    return get_schema_example("bulk_api/command/create_group_membership.json")
