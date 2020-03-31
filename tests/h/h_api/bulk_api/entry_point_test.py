import json
from copy import deepcopy
from io import BytesIO, StringIO
from types import GeneratorType
from unittest.mock import sentinel

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

    @pytest.mark.parametrize(
        "input_data,bulk_method",
        (
            ("lines", BulkAPI.from_lines),
            ("nd_json", BulkAPI.from_string),
            ("nd_json_byte_stream", BulkAPI.from_byte_stream),
        ),
        indirect=["input_data"],
    )
    def test_from_input(self, input_data, executor, bulk_method, CommandProcessor):
        result = bulk_method(input_data, executor)

        CommandProcessor.assert_called_once_with(
            executor=executor, observer=Any.instance_of(Observer)
        )
        assert result == sentinel.reports
        self._assert_process_called_with_generator_of_commands(CommandProcessor)

    def test__bytes_to_lines(self):
        bytes = BytesIO(b"\nline_1\n\nlong_middle_line_2\nline_3")

        lines = BulkAPI._bytes_to_lines(bytes, chunk_size=8)

        assert isinstance(lines, GeneratorType)
        assert list(lines) == [b"line_1", b"long_middle_line_2", b"line_3"]

    def test__string_to_lines(self):
        lines = BulkAPI._string_to_lines("\nline_1\n\nlong_middle_line_2\nline_3")

        assert isinstance(lines, GeneratorType)
        assert list(lines) == ["line_1", "long_middle_line_2", "line_3"]

    @pytest.mark.parametrize(
        "kwargs",
        (
            pytest.param({"executor": "not an executor"}, id="bad executor"),
            pytest.param({"observer": "not an observer"}, id="bad observer"),
        ),
    )
    @pytest.mark.parametrize("method", (BulkAPI.from_lines, BulkAPI.from_string))
    def test_we_reject_bad_arguments(self, method, kwargs, executor):
        kwargs.setdefault("executor", executor)

        with pytest.raises(TypeError):
            method("any string", **kwargs)

    def test_to_stream(self, commands):
        handle = StringIO()

        expected = deepcopy([command.raw for command in commands])

        BulkAPI.to_stream(handle, commands)

        assert self._decode_ndjson(handle.getvalue()) == expected

    def test_to_string(self, commands):
        expected = deepcopy([command.raw for command in commands])

        nd_json = BulkAPI.to_string(commands)

        assert self._decode_ndjson(nd_json) == expected

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

    def _decode_ndjson(self, nd_json):
        return [json.loads(data) for data in nd_json.strip().split("\n")]

    @pytest.fixture
    def commands(self, config_command, user_command):
        return [config_command, user_command]

    @pytest.fixture
    def CommandProcessor(self, patch):
        CommandProcessor = patch("h.h_api.bulk_api.entry_point.CommandProcessor")

        CommandProcessor.return_value.process.return_value = sentinel.reports

        return CommandProcessor

    @pytest.fixture
    def input_data(self, request):
        return request.getfixturevalue(request.param)

    @pytest.fixture
    def nd_json(self):
        return resource_string("tests", "h/h_api/fixtures/bulk_api.ndjson").decode(
            "utf-8"
        )

    @pytest.fixture
    def nd_json_byte_stream(self, nd_json):
        return BytesIO(nd_json.encode("utf-8"))

    @pytest.fixture
    def lines(self, nd_json):
        return nd_json.strip().split("\n")
