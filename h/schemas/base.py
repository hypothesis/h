"""Shared functionality for schemas."""

import copy

import colander
import deform
import jsonschema
from pyramid import httpexceptions
from pyramid.csrf import check_csrf_token, get_csrf_token


@colander.deferred
def deferred_csrf_token(_node, kwargs):
    request = kwargs.get("request")
    return get_csrf_token(request)


class ValidationError(
    httpexceptions.HTTPBadRequest
):  # pylint: disable=too-many-ancestors
    pass


class CSRFSchema(colander.Schema):
    """
    A CSRFSchema backward-compatible with the one from the hem module.

    Unlike hem, this doesn't require that the csrf_token appear in the
    serialized appstruct.
    """

    csrf_token = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.HiddenWidget(),
        default=deferred_csrf_token,
        missing=None,
    )

    def validator(self, node, _value):  # pylint: disable=no-self-use
        request = node.bindings["request"]
        check_csrf_token(request)


class JSONSchema:
    """
    Validate data according to a Draft 4 JSON Schema.

    Inherit from this class and override the `schema` class property with a
    valid JSON schema.
    """

    schema = {}

    def __init__(self):
        format_checker = jsonschema.FormatChecker()
        self.validator = jsonschema.Draft4Validator(
            self.schema, format_checker=format_checker
        )

    def validate(self, data):
        """
        Validate `data` according to the current schema.

        :param data: The data to be validated
        :returns: valid data
        :raises ~h.schemas.ValidationError: if the data is invalid
        """
        # Take a copy to ensure we don't modify what we were passed.
        appstruct = copy.deepcopy(data)

        errors = list(self.validator.iter_errors(appstruct))
        if errors:
            msg = ", ".join([_format_jsonschema_error(e) for e in errors])
            raise ValidationError(msg)
        return appstruct


def enum_type(enum_cls):
    """
    Return a `colander.Type` implementation for a field with a given enum type.

    :param enum_cls: The enum class
    :type enum_cls: enum.Enum
    """

    class EnumType(colander.SchemaType):
        def deserialize(self, node, cstruct):  # pylint: disable= no-self-use
            if cstruct == colander.null:
                return None

            try:
                return enum_cls[cstruct]
            except KeyError as err:
                msg = f'"{cstruct}" is not a known value'
                raise colander.Invalid(node, msg) from err

        def serialize(self, _node, appstruct):  # pylint: disable= no-self-use
            if not appstruct:
                return ""
            return appstruct.name

    return EnumType


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = ".".join([str(c) for c in error.path])
        return f"{dotted_path}: {error.message}"
    return error.message
