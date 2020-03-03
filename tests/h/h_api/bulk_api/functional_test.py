import json
from io import StringIO
from unittest.mock import call, create_autospec

import pytest
from h_matchers import Any
from pkg_resources import resource_filename

from h.h_api.bulk_api import BulkAPI, CommandBuilder
from h.h_api.bulk_api.executor import Executor, FakeReportExecutor
from h.h_api.bulk_api.model.command import DataCommand
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.bulk_api.observer import DebugObserver
from h.h_api.enums import CommandType, DataType


class TestBulkAPIFunctional:
    def test_command_parsing_ok(self, executor):
        fixture = resource_filename("tests", "h/h_api/fixtures/bulk_api.ndjson")

        with open(fixture) as lines:
            BulkAPI.from_stream(lines, executor=executor, observer=DebugObserver())

        executor.configure.assert_called_with(config=Any.instance_of(Configuration))

        executor.execute_batch.assert_has_calls(
            [
                call(
                    command_type=CommandType.UPSERT,
                    data_type=DataType.USER,
                    batch=[Any.instance_of(DataCommand)],
                    default_config={},
                ),
                call(
                    command_type=CommandType.UPSERT,
                    data_type=DataType.GROUP,
                    batch=[Any.instance_of(DataCommand)],
                    default_config={},
                ),
                call(
                    command_type=CommandType.CREATE,
                    data_type=DataType.GROUP_MEMBERSHIP,
                    batch=[Any.instance_of(DataCommand)],
                    default_config={"on_duplicate": "continue"},
                ),
            ]
        )

    def test_command_serialisation_ok(self):
        """A sanity check that hits most of the behavior of creation.

        This is a happy path check. We expect this to work."""

        handle = StringIO()

        BulkAPI.to_stream(handle, self.yield_commands())

        ndjson = handle.getvalue()
        lines = ndjson.strip().split("\n")
        command_data = [json.loads(line) for line in lines]

        assert len(command_data) == 4

        assert command_data == [
            ["configure", Any.dict()],
            ["upsert", {"data": Any.dict.containing({"type": "user"})}],
            ["upsert", {"data": Any.dict.containing({"type": "group"})}],
            ["create", {"data": Any.dict.containing({"type": "group_membership"})}],
        ]

    @staticmethod
    def yield_commands():
        yield CommandBuilder.configure(
            effective_user="acct:user@example.com",
            # The instruction count includes this one
            total_instructions=4,
        )

        user_id = "acct:user@wat.com"

        yield CommandBuilder.user.upsert(
            user_id,
            {
                "username": "username",
                "display_name": "display name",
                "authority": "authority",
                "identities": [
                    {"provider": "provider", "provider_unique_id": "provider_unique_id"}
                ],
            },
        )

        group_ref = "group_ref"

        yield CommandBuilder.group.upsert(
            {"groupid": "group:groupid@example.com", "name": "group:name@example.com"},
            id_reference=group_ref,
        )

        yield CommandBuilder.group_membership.create(user_id, group_ref)

    @pytest.fixture
    def executor(self):
        executor = create_autospec(Executor, instance=True)
        bound_execute = FakeReportExecutor.execute_batch.__get__(
            executor, executor.__class__
        )
        executor.execute_batch.side_effect = bound_execute

        return executor
