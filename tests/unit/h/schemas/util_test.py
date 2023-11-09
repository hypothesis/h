import colander
import pytest
from webob.multidict import MultiDict

from h.schemas.base import ValidationError
from h.schemas.util import validate_query_params


class QueryParamSchema(colander.Schema):
    int_field = colander.SchemaNode(colander.Integer(), missing=0)

    string_field = colander.SchemaNode(colander.String(), missing=None)

    list_field = colander.SchemaNode(
        colander.Sequence(), colander.SchemaNode(colander.String()), missing=None
    )

    enum_field = colander.SchemaNode(
        colander.String(), validator=colander.OneOf(["up", "down"]), missing="up"
    )

    drop_if_not_set_field = colander.SchemaNode(
        colander.String(), missing=colander.drop
    )


class TestValidateQueryParams:
    def test_it_deserializes_params(self):
        schema = QueryParamSchema()
        params = MultiDict()
        params.add("string_field", "test")

        parsed = validate_query_params(schema, params)

        assert parsed == {
            "int_field": 0,
            "string_field": "test",
            "list_field": None,
            "enum_field": "up",
        }

    def test_it_raises_if_params_invalid(self):
        schema = QueryParamSchema()
        params = MultiDict({"int_field": "not-an-int"})

        with pytest.raises(ValidationError):
            validate_query_params(schema, params)

    def test_it_keeps_all_values_for_sequence_fields(self):
        schema = QueryParamSchema()
        params = MultiDict()
        params.add("list_field", "first")
        params.add("list_field", "second")

        parsed = validate_query_params(schema, params)

        assert parsed.getall("list_field") == ["first", "second"]

    def test_a_list_field_can_have_a_single_value(self):
        schema = QueryParamSchema()
        params = MultiDict()
        params.add("list_field", "first")

        parsed = validate_query_params(schema, params)

        assert parsed.getall("list_field") == ["first"]

    def test_it_keeps_only_last_value_for_non_sequence_fields(self):
        schema = QueryParamSchema()
        params = MultiDict()
        params.add("string_field", "first")
        params.add("string_field", "second")

        parsed = validate_query_params(schema, params)

        assert parsed.getall("string_field") == ["second"]

    def test_it_does_not_include_unknown_fields(self):
        schema = QueryParamSchema()
        params = MultiDict()
        params.add("string_field", "include_me")
        params.add("unknown_field", "ignore_me")

        parsed = validate_query_params(schema, params)

        assert "unknown_field" not in parsed
