from copy import deepcopy
from unittest.mock import create_autospec

import pytest

from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.bulk_api.executor import AutomaticReportExecutor, Executor
from h.h_api.schema import Schema


def get_schema_example(schema_path):
    return deepcopy(Schema.get_schema(schema_path)["examples"][0])


@pytest.fixture
def config_command():
    return CommandBuilder.configure(
        effective_user="acct:user@example.com", total_instructions=2
    )


@pytest.fixture
def group_command(group_attributes):
    return CommandBuilder.group.upsert(group_attributes, "group_ref")


@pytest.fixture
def user_command(user_attributes):
    return CommandBuilder.user.upsert(user_attributes, "user_ref")


@pytest.fixture
def membership_command(user_command, group_command):
    return CommandBuilder.group_membership.create(
        user_ref=user_command.body.id_reference,
        group_ref=group_command.body.id_reference,
    )


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


@pytest.fixture
def executor():
    executor = create_autospec(Executor, instance=True)
    fake_report_executor = AutomaticReportExecutor()

    executor.execute_batch.side_effect = fake_report_executor.execute_batch

    return executor
