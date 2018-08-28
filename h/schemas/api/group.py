# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander

from h.schemas.base import JSONSchema
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
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
            'description': {
                'type': 'string',
                'maxLength': GROUP_DESCRIPTION_MAX_LENGTH,
            },
        },
        'required': [
            'name'
        ],
    }


class GetGroupsAPISchema(colander.Schema):
    """Query parameter schema for `GET /api/groups`."""

    authority = colander.SchemaNode(colander.String(),
                                    missing=None,
                                    description="Domain of authority to fetch groups for")

    document_uri = colander.SchemaNode(colander.String(),
                                       validator=colander.url,
                                       missing=None,
                                       description="Include public groups associated with this URL")

    expand = colander.SchemaNode(colander.Sequence(),
                                 colander.SchemaNode(colander.String(),
                                                     validator=colander.OneOf(["organization"])),
                                 missing=[],
                                 description="Sub-fields to expand in the response")
