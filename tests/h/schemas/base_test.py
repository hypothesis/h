import enum
from unittest.mock import Mock

import colander
import pytest
from pyramid import csrf
from pyramid.exceptions import BadCSRFToken

from h.schemas import ValidationError
from h.schemas.base import CSRFSchema, JSONSchema, enum_type

pytestmark = pytest.mark.usefixtures("pyramid_config")


class ExampleCSRFSchema(CSRFSchema):
    pass


class ExampleJSONSchema(JSONSchema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {"foo": {"type": "string"}, "bar": {"type": "integer"}},
        "required": ["foo", "bar"],
    }


class TestCSRFSchema:
    def test_raises_badcsrf_with_bad_csrf(self, pyramid_request):
        schema = ExampleCSRFSchema().bind(request=pyramid_request)

        with pytest.raises(BadCSRFToken):
            schema.deserialize({})

    def test_ok_with_good_csrf(self, pyramid_request):
        csrf_token = csrf.get_csrf_token(pyramid_request)
        pyramid_request.POST["csrf_token"] = csrf_token
        schema = ExampleCSRFSchema().bind(request=pyramid_request)

        # Does not raise
        schema.deserialize({})

    def test_ok_with_good_csrf_from_header(self, pyramid_csrf_request):
        schema = ExampleCSRFSchema().bind(request=pyramid_csrf_request)

        # Does not raise
        schema.deserialize({})


class TestJSONSchema:
    def test_it_raises_for_unsupported_schema_versions(self):
        class BadSchema(JSONSchema):
            schema_version = 95

        with pytest.raises(ValueError):
            BadSchema()

    def test_it_returns_data_when_valid(self):
        data = {"foo": "baz", "bar": 123}

        assert ExampleJSONSchema().validate(data) == data

    def test_it_raises_when_data_invalid(self):
        data = 123  # not an object

        with pytest.raises(ValidationError):
            ExampleJSONSchema().validate(data)

    def test_it_sets_appropriate_error_message_when_data_invalid(self):
        data = {"foo": "baz"}  # required bar is missing

        with pytest.raises(ValidationError) as e:
            ExampleJSONSchema().validate(data)

        message = str(e.value)
        assert message.startswith("'bar' is a required property")

    def test_it_returns_all_errors_in_message(self):
        data = {}  # missing both required fields

        with pytest.raises(ValidationError) as e:
            ExampleJSONSchema().validate(data)

        message = str(e.value)
        assert message.startswith(
            "'foo' is a required property, 'bar' is a required property"
        )


class Color(enum.Enum):
    RED = "#ff0000"
    GREEN = "#00ff00"
    BLUE = "#0000ff"


class TestEnumType:
    def test_serialize_returns_a_string(self, color_type):
        node = Mock()
        assert color_type.serialize(node, Color.RED) == "RED"

    def test_serialize_returns_an_empty_string_if_value_is_none(self, color_type):
        node = Mock()
        assert not color_type.serialize(node, None)

    def test_deserialize_returns_none_if_value_is_null(self, color_type):
        node = Mock()
        assert color_type.deserialize(node, colander.null) is None

    def test_deserialize_returns_an_enum(self, color_type):
        node = Mock()
        assert color_type.deserialize(node, "RED") == Color.RED

    def test_deserialize_raises_if_value_unknown(self, color_type):
        node = Mock()
        with pytest.raises(colander.Invalid):
            color_type.deserialize(node, "rebeccapurple")

    @pytest.fixture
    def color_type(self):
        return enum_type(Color)()
