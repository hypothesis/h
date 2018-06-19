# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.schemas.base import JSONSchema
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
)


class CreateGroupAPISchema(JSONSchema):
    """Validates a JSON payload for creating a new group via API"""
    schema = {
        'type': 'object',
        'properties': {
            'name': {
                'type': 'string',
                'minLength': GROUP_NAME_MIN_LENGTH,
                'maxLength': GROUP_NAME_MAX_LENGTH,
            },
        },
        'required': [
            'name'
        ],
    }
