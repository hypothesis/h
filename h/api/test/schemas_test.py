# -*- coding: utf-8 -*-
import pytest

from h.api import schemas


class ExampleSchema(schemas.JSONSchema):
    schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'string',
    }


def test_jsonschema_returns_data_when_valid():
    data = "a string"

    assert ExampleSchema().validate(data) == data


def test_jsonschema_raises_when_data_invalid():
    data = 123  # not a string

    with pytest.raises(schemas.ValidationError):
        ExampleSchema().validate(data)


def test_jsonschema_sets_appropriate_error_message_when_data_invalid():
    data = 123  # not a string

    with pytest.raises(schemas.ValidationError) as e:
        ExampleSchema().validate(data)

    message = e.value.message
    assert message.startswith("123 is not of type 'string'")


@pytest.mark.parametrize('field', [
    'created',
    'updated',
    'user',
    'id',
])
def test_annotationschema_removes_protected_fields(field):
    data = {}
    data[field] = 'something forbidden'

    result = schemas.AnnotationSchema().validate(data)

    assert field not in result
