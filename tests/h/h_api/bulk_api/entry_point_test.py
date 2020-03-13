import json
from io import StringIO
from types import GeneratorType

import pytest
from h_matchers import Any
from pkg_resources import resource_string

from h.h_api.bulk_api import BulkAPI
from h.h_api.bulk_api.model.command import Command
from h.h_api.bulk_api.observer import Observer
from h.h_api.exceptions import InvalidJSONError


class TestBulkAPI:
    # This is a glue library, so there's not much to do here but test the
    # interfaces

    def test_from_stream(self, lines, executor, CommandProcessor):
        BulkAPI.from_stream(lines, executor)

        CommandProcessor.assert_called_once_with(
            executor=executor, observer=Any.instance_of(Observer)
        )

        self._assert_process_called_with_generator_of_commands(CommandProcessor)

    def test_from_string(self, nd_json, executor, CommandProcessor):
        BulkAPI.from_string(nd_json, executor)

        CommandProcessor.assert_called_once_with(
            executor=executor, observer=Any.instance_of(Observer)
        )

        self._assert_process_called_with_generator_of_commands(CommandProcessor)

    @pytest.mark.parametrize(
        "kwargs",
        (
            pytest.param({"executor": "not an executor"}, id="bad executor"),
            pytest.param({"observer": "not an observer"}, id="bad observer"),
        ),
    )
    @pytest.mark.parametrize("method", (BulkAPI.from_stream, BulkAPI.from_string))
    def test_we_reject_bad_arguments(self, method, kwargs, executor):
        kwargs.setdefault("executor", executor)

        with pytest.raises(TypeError):
            method("any string", **kwargs)

    def test_to_stream(self, commands):
        handle = StringIO()

        BulkAPI.to_stream(handle, commands)

        self._assert_nd_json_matches_commands(handle.getvalue(), commands)

    def test_to_string(self, commands):
        nd_json = BulkAPI.to_string(commands)

        self._assert_nd_json_matches_commands(nd_json, commands)

    def test_we_catch_json_parsing_errors(self, config_command, executor):
        bad_string = json.dumps(config_command.raw) + '\n["Nonsense'

        with pytest.raises(InvalidJSONError):
            BulkAPI.from_string(bad_string, executor)

    def _assert_process_called_with_generator_of_commands(self, CommandProcessor):
        (generator,), _ = CommandProcessor.return_value.process.call_args

        assert isinstance(generator, GeneratorType)
        assert generator == Any.iterable.comprised_of(Any.instance_of(Command)).of_size(
            4
        )

    def _assert_nd_json_matches_commands(self, nd_json, commands):
        data = [json.loads(data) for data in nd_json.strip().split("\n")]
        assert data == [command.raw for command in commands]

    @pytest.fixture
    def commands(self, config_command, user_command):
        return [config_command, user_command]

    @pytest.fixture
    def CommandProcessor(self, patch):
        return patch("h.h_api.bulk_api.entry_point.CommandProcessor")

    @pytest.fixture
    def nd_json(self):
        return resource_string("tests", "h/h_api/fixtures/bulk_api.ndjson").decode(
            "utf-8"
        )

    @pytest.fixture
    def lines(self, nd_json):
        return nd_json.strip().split("\n")
