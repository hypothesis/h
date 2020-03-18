import json
from io import BytesIO
from unittest.mock import call

import pytest
from h_matchers import Any
from pkg_resources import resource_string

from h.h_api.bulk_api import BulkAPI, CommandBuilder
from h.h_api.bulk_api.executor import AutomaticReportExecutor
from h.h_api.bulk_api.model.command import DataCommand
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.bulk_api.observer import Observer
from h.h_api.enums import CommandStatus, CommandType, DataType


class TestBulkAPIFunctional:
    def test_command_parsing_ok(self, executor, ndjson_bytes):
        """Sanity test that hits most elements of parsing."""

        BulkAPI.from_byte_stream(ndjson_bytes, executor=executor, observer=Observer())

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

    def test_command_serialisation_ok(self, commands):
        """A sanity check that hits most of the behavior of creation.

        This is a happy path check. We expect this to work."""

        ndjson = BulkAPI.to_string(commands)
        lines = ndjson.strip().split("\n")
        command_data = [json.loads(line) for line in lines]

        assert len(command_data) == 4

        assert command_data == [
            ["configure", Any.dict()],
            ["upsert", {"data": Any.dict.containing({"type": "user"})}],
            ["upsert", {"data": Any.dict.containing({"type": "group"})}],
            ["create", {"data": Any.dict.containing({"type": "group_membership"})}],
        ]

    def test_round_tripping(self, commands, collecting_observer):
        """Check that sending and decoding results in the same data."""

        original_raw = [command.raw for command in commands]

        BulkAPI.from_byte_stream(
            BytesIO(BulkAPI.to_string(commands).encode("utf-8")),
            executor=AutomaticReportExecutor(),
            observer=collecting_observer,
        )

        final_raw = [command.raw for command in collecting_observer.commands]

        assert original_raw == final_raw

    @pytest.fixture
    def collecting_observer(self):
        class CollectingObserver(Observer):
            commands = []

            def observe_command(self, command, status):
                if status == CommandStatus.AS_RECEIVED:
                    self.commands.append(command)

        return CollectingObserver()

    @pytest.fixture
    def commands(self, user_command, group_command, membership_command):
        return (
            CommandBuilder.configure("acct:user@example.com", total_instructions=4),
            user_command,
            group_command,
            membership_command,
        )

    @pytest.fixture
    def ndjson_bytes(self):
        return BytesIO(resource_string("tests", "h/h_api/fixtures/bulk_api.ndjson"))
