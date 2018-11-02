# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.schemas.base import JSONSchema, ValidationError
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
    AUTHORITY_PROVIDED_ID_PATTERN,
    AUTHORITY_PROVIDED_ID_MAX_LENGTH,
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
            'groupid': {
                'type': 'string',
                'pattern': AUTHORITY_PROVIDED_ID_PATTERN,
                'maxLength': AUTHORITY_PROVIDED_ID_MAX_LENGTH,
            },
        },
        'required': [
            'name'
        ],
    }

    @staticmethod
    def validate_groupid(appstruct, group_authority, default_authority):
        """
        Validate the groupid property. A non-None groupid is only allowed if the
        authority the group will be associated with is not the default authority
        (i.e. third-party authority only)

        :raises ValidationError: if ``groupid`` is not allowed for the applied authority
        """
        groupid = appstruct.get('groupid', None)
        if groupid is None:
            return

        if (group_authority is None) or (group_authority == default_authority):
            raise ValidationError('`groupid` may not be set for groups in the default authority')
