# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import enum
from mock import Mock
import pytest

import colander
from pyramid.exceptions import BadCSRFToken

from h.schemas import ValidationError
from h.schemas.base import enum_type, CSRFSchema, JSONSchema


class ExampleCSRFSchema(CSRFSchema):
    pass


class ExampleJSONSchema(JSONSchema):
    schema = {
        b'$schema': b'http://json-schema.org/draft-04/schema#',
        b'type': b'object',
        b'properties': {
            b'foo': {b'type': b'string'},
            b'bar': {b'type': b'integer'},
        },
        b'required': [b'foo', b'bar'],
    }


class TestCSRFSchema(object):
    def test_raises_badcsrf_with_bad_csrf(self, pyramid_request):
        schema = ExampleCSRFSchema().bind(request=pyramid_request)

        with pytest.raises(BadCSRFToken):
            schema.deserialize({})

    def test_ok_with_good_csrf(self, pyramid_request):
        csrf_token = pyramid_request.session.get_csrf_token()
        pyramid_request.POST['csrf_token'] = csrf_token
        schema = ExampleCSRFSchema().bind(request=pyramid_request)

        # Does not raise
        schema.deserialize({})

    def test_ok_with_good_csrf_from_header(self, pyramid_csrf_request):
        schema = ExampleCSRFSchema().bind(request=pyramid_csrf_request)

        # Does not raise
        schema.deserialize({})


class TestJSONSchema(object):
    def test_it_returns_data_when_valid(self):
        data = {'foo': 'baz', 'bar': 123}

        assert ExampleJSONSchema().validate(data) == data

    def test_it_raises_when_data_invalid(self):
        data = 123  # not an object

        with pytest.raises(ValidationError):
            ExampleJSONSchema().validate(data)

    def test_it_sets_appropriate_error_message_when_data_invalid(self):
        data = {'foo': 'baz'}  # required bar is missing

        with pytest.raises(ValidationError) as e:
            ExampleJSONSchema().validate(data)

        message = e.value.message
        assert message.startswith("'bar' is a required property")

    def test_it_returns_all_errors_in_message(self):
        data = {}  # missing both required fields

        with pytest.raises(ValidationError) as e:
            ExampleJSONSchema().validate(data)

        message = e.value.message
        assert message.startswith("'foo' is a required property, 'bar' is a required property")


class Color(enum.Enum):
        red = '#ff0000'
        green = '#00ff00'
        blue = '#0000ff'


class TestEnumType(object):

    def test_serialize_returns_a_string(self, color_type):
        node = Mock()
        assert color_type.serialize(node, Color.red) == 'red'

    def test_serialize_returns_an_empty_string_if_value_is_none(self, color_type):
        node = Mock()
        assert color_type.serialize(node, None) == ''

    def test_deserialize_returns_none_if_value_is_null(self, color_type):
        node = Mock()
        assert color_type.deserialize(node, colander.null) is None

    def test_deserialize_returns_an_enum(self, color_type):
        node = Mock()
        assert color_type.deserialize(node, 'red') == Color.red

    def test_deserialize_raises_if_value_unknown(self, color_type):
        node = Mock()
        with pytest.raises(colander.Invalid):
            color_type.deserialize(node, 'rebeccapurple')

    @pytest.fixture
    def color_type(self):
        return enum_type(Color)()
