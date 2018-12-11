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
        "type": "object",
        "properties": {
            "authority": {"type": "string", "format": "hostname"},
            "username": {
                "type": "string",
                "minLength": USERNAME_MIN_LENGTH,
                "maxLength": USERNAME_MAX_LENGTH,
                "pattern": "^[A-Za-z0-9._]+$",
            },
            "email": {
                "type": "string",
                "format": "email",
                "maxLength": EMAIL_MAX_LENGTH,
            },
            "display_name": {"type": "string", "maxLength": DISPLAY_NAME_MAX_LENGTH},
            "identities": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string"},
                        "provider_unique_id": {"type": "string"},
                    },
                    "required": ["provider", "provider_unique_id"],
                },
            },
        },
        "anyOf": [  # email may be empty if identities are present
            {"required": ["authority", "username", "email"]},
            {"required": ["authority", "username", "identities"]},
        ],
    }

    def validate(self, data):
        appstruct = super(CreateUserAPISchema, self).validate(data)
        return appstruct


class UpdateUserAPISchema(JSONSchema):
    """Validate a user JSON object."""

    schema = {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "format": "email",
                "maxLength": EMAIL_MAX_LENGTH,
            },
            "display_name": {"type": "string", "maxLength": DISPLAY_NAME_MAX_LENGTH},
        },
    }

    def validate(self, data):
        appstruct = super(UpdateUserAPISchema, self).validate(data)
        appstruct = self._whitelisted_properties_only(appstruct)
        return appstruct

    def _whitelisted_properties_only(self, appstruct):
        """Return a new appstruct containing only schema-defined fields"""

        new_appstruct = {}

        for allowed_field in UpdateUserAPISchema.schema["properties"].keys():
            if allowed_field in appstruct:
                new_appstruct[allowed_field] = appstruct[allowed_field]

        return new_appstruct
