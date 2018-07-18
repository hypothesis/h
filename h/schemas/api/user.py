# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models.user import (
    DISPLAY_NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)
from h.schemas.base import JSONSchema


class CreateUserAPISchema(JSONSchema):
    """Validate a user JSON object."""

    schema = {
        'type': 'object',
        'properties': {
            'authority': {
                'type': 'string',
                'format': 'hostname',
            },
            'username': {
                'type': 'string',
                'minLength': USERNAME_MIN_LENGTH,
                'maxLength': USERNAME_MAX_LENGTH,
                'pattern': '^[A-Za-z0-9._]+$',
            },
            'email': {
                'type': 'string',
                'format': 'email',
                'maxLength': EMAIL_MAX_LENGTH,
            },
            'display_name': {
                'type': 'string',
                'maxLength': DISPLAY_NAME_MAX_LENGTH,
            },
        },
        'required': [
            'authority',
            'username',
        ],
    }


class UpdateUserAPISchema(JSONSchema):
    """Validate a user JSON object."""

    schema = {
        'type': 'object',
        'properties': {
            'email': {
                'type': 'string',
                'format': 'email',
                'maxLength': EMAIL_MAX_LENGTH,
            },
            'display_name': {
                'type': 'string',
                'maxLength': DISPLAY_NAME_MAX_LENGTH,
            },
        },
    }
