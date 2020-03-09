import pytest
from h_matchers import Any

from h.h_api.exceptions import SchemaValidationError
from h.h_api.schema import Schema, Validator


class TestValidator:
    def test_validate_ok(self, validator):
        validator.validate_all({"a": "a", "b": "b"})

    def test_validation_fail(self, validator):
        error = None
        try:
            validator.validate_all({"a": 1})
        except SchemaValidationError as err:
            error = err

        assert isinstance(error, SchemaValidationError)

        assert [body.raw for body in error.error_bodies] == [
            Any.dict.containing({"source": {"pointer": "a"}}),
            Any.dict.containing(
                {"meta": Any.dict.containing({"schema": {"pointer": "required"}})}
            ),
        ]

    @pytest.fixture
    def validator(self):
        return Validator(
            {
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "required": ["a", "b"],
            }
        )


class TestSchema:
    def test_get_validator(self, upsert_group_body):
        validator = Schema.get_validator("bulk_api/command/upsert_group.json")

        assert isinstance(validator, Validator)

        # Check something that should pass
        validator.validate_all(upsert_group_body)

    def test_get_validator_configured_to_load_referenced_schema(
        self, upsert_group_body
    ):
        validator = Schema.get_validator("bulk_api/command/upsert_group.json")

        # Modify one value which proves we configured the Validator to load
        # chained schema
        upsert_group_body["data"]["meta"]["query"]["groupid"] = "wrong_pattern"

        with pytest.raises(SchemaValidationError):
            validator.validate_all(upsert_group_body)

    def test_get_schema(self):
        schema = Schema.get_schema("core.json#/$defs/userId")

        assert isinstance(schema, dict)
        assert schema["type"] == "string"
