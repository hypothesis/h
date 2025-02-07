"""Shared functionality for schemas."""

import copy

import colander
import deform
import jsonschema
from pyramid import httpexceptions
from pyramid.csrf import get_csrf_token


@colander.deferred
def deferred_csrf_token(_node, kwargs):
    request = kwargs.get("request")
    return get_csrf_token(request)


class ValidationError(httpexceptions.HTTPBadRequest):
    pass


class CSRFSchema(colander.Schema):
    """
    Add a hidden CSRF token to forms when seralized using Deform.

    This is intended as a base class for other schemas to inherit from if the
    schema's form needs a CSRF token (by default all form submissions do need a
    CSRF token).

    This schema *does not* implement CSRF verification when receiving requests.
    That's enabled globally for non-GET requests by
    config.set_default_csrf_options(require_csrf=True).
    """

    csrf_token = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.HiddenWidget(),
        # When serializing (i.e. when rendering a form) if there's no
        # csrf_token then call deferred_csrf_token() to get one.
        default=deferred_csrf_token,
        # Allow data with no "csrf_token" field to be *deserialized* successfully
        # (the deserialized data will contain no "csrf_token" field.)
        #
        # CSRF protection isn't provided by this schema, it's provided by
        # Pyramid's config.set_default_csrf_options(require_csrf=True).
        #
        # Nonetheless, without a `missing` value, when deserializing any
        # subclass of this schema Colander would require a csrf_token field to
        # be present in the data (even if this schema doesn't actually check
        # that the token is valid).
        #
        # In production any request missing a CSRF token would be rejected by
        # Pyramid's CSRF protection before even reaching schema
        # deserialization. So by the time we get to schema deserialization
        # there must be a CSRF token and this `missing` value is seemingly
        # unnecessary.
        #
        # However:
        #
        # 1. The CSRF token may be in an X-CSRF-Token header rather than in a
        #    POST param.
        # 2. Unittests for schemas often don't set a CSRF token and would fail
        #    if this `missing` value wasn't here.
        missing=colander.drop,
    )


class JSONSchema:
    """
    Validate data according to a JSON Schema.

    Inherit from this class and override the `schema` class property with a
    valid JSON schema.
    """

    schema = {}  # noqa: RUF012

    schema_version = 4
    """The JSON Schema version used by this schema."""

    def __init__(self):
        format_checker = jsonschema.FormatChecker()

        if self.schema_version == 4:
            validator_cls = jsonschema.Draft4Validator
        elif self.schema_version == 7:
            validator_cls = jsonschema.Draft7Validator
        else:
            raise ValueError("Unsupported schema version")  # noqa: EM101, TRY003

        self.validator = validator_cls(self.schema, format_checker=format_checker)

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
        def deserialize(self, node, cstruct):
            if cstruct == colander.null:
                return None

            try:
                return enum_cls[cstruct]
            except KeyError as err:
                msg = f'"{cstruct}" is not a known value'
                raise colander.Invalid(node, msg) from err

        def serialize(self, _node, appstruct):
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
