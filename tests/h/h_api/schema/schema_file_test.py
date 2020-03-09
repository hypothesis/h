import os

import pytest
from jsonschema import Draft7Validator

from h.h_api.schema import Schema


def schema_file_names():
    for path, _, names in os.walk(Schema.BASE_DIR):
        for name in names:
            full_path = os.path.join(path, name)
            rel_path = os.path.relpath(full_path, Schema.BASE_DIR)

            yield rel_path


def schema_with_examples():
    for file_name in schema_file_names():
        schema = Schema.get_schema(file_name)

        if "examples" in schema:
            yield file_name

        defs = schema.get("$defs")
        if not defs:
            continue

        for key, sub_schema in defs.items():
            if "examples" in sub_schema:
                yield f"{file_name}#/$defs/{key}"


class TestSchemaFiles:
    def test_schema_is_a_valid_schema(self, schema_path):
        schema = Schema.get_schema(schema_path)
        Draft7Validator.check_schema(schema)

    def test_schema_match_their_examples(self, schema_path_with_example):
        schema = Schema.get_schema(schema_path_with_example)
        validator = Schema.get_validator(schema_path_with_example)
        examples = schema["examples"]

        for example in examples:
            validator.validate_all(example)

    @pytest.fixture(params=schema_with_examples())
    def schema_path_with_example(self, request):
        return request.param

    @pytest.fixture(params=schema_file_names())
    def schema_path(self, request):
        return request.param
