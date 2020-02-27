import pytest
from h_matchers import Any
from jsonschema import Draft7Validator

from h.h_api.exceptions import JSONAPIException, SchemaValidationError
from h.h_api.model.json_api import JSONAPIErrorBody


class TestJSONAPIExcepion:
    def test_subclassing(self):
        body = JSONAPIErrorBody.create(KeyError("test"))

        class TestError(JSONAPIException):
            def _error_bodies(self):
                yield body

        error = TestError("Name")

        assert error.as_dict() == {"errors": [body.raw]}


class TestSchemaValidationError:
    def test_add_error(self, json_schema_error, JSONAPIErrorBody):
        error = SchemaValidationError()

        assert error.error_bodies == []
        error.add_error(json_schema_error)

        assert error.error_bodies == [JSONAPIErrorBody.create.return_value]

        JSONAPIErrorBody.create.assert_called_once_with(
            error,
            detail=Any.string(),
            meta={"schema": {"pointer": "properties/a/type"}, "context": []},
            pointer="a",
        )

    def test_has_errors(self, json_schema_error):
        error = SchemaValidationError()

        assert not error.has_errors()
        error.add_error(json_schema_error)
        assert error.has_errors()

    @pytest.fixture
    def JSONAPIErrorBody(self, patch):
        return patch("h.h_api.exceptions.JSONAPIErrorBody")

    @pytest.fixture
    def json_schema_error(self):
        schema = {"type": "object", "properties": {"a": {"type": "string"}}}

        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors({"a": 1}))

        return errors[0]
