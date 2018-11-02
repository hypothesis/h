# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.schemas.base import JSONSchema, ValidationError
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
)
from h.util.group import GROUPID_PATTERN, split_groupid


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
                'pattern': GROUPID_PATTERN,
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
        (i.e. third-party authority only).

        Mutates and returns ``appstruct``, adding ``groupid`` entries if present
        and valid.

        :param group_authority:   The authority that is be associated with the group
        :param default_authority: The service's default authority; if it is the same as
                                  ``group_authority``, then this is considered a
                                  "first-party" group
        :raises ValidationError: * if ``groupid`` is not allowed for the applied authority
                                 * if ``groupid`` is not in proper format
                                 * if the ``authority`` part of ``groupid`` does not match
                                   the group (client) authority
        :rtype: dict or None
        :return: the groupid parts or None
        """
        groupid = appstruct.get('groupid', None)
        if groupid is None:
            return appstruct

        if (group_authority is None) or (group_authority == default_authority):
            raise ValidationError(
                "groupid may only be set on groups oustide of the default authority '{authority}'".format(
                    authority=default_authority
                ))

        try:
            groupid_parts = split_groupid(groupid)
        except ValueError:
            raise ValidationError("'{groupid}' does not match valid groupid format: '{pattern}'".format(
                groupid=groupid,
                pattern=GROUPID_PATTERN))

        if groupid_parts['authority'] != group_authority:
            raise ValidationError("Invalid authority '{authority}' in groupid '{groupid}'".format(
                authority=groupid_parts['authority'],
                groupid=groupid))

        return groupid_parts
