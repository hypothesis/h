# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Classes for validating manually-imported annotations."""

from h.schemas.base import JSONSchema


class AnnotationImportSchema(JSONSchema):

    """Validate an annotation for import.

    This schema is based on the W3C Web Annotation model, but only implements
    the subset of the specification we need for importing purposes.
    """

    schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'properties': {
            '@context': {
                'enum': ['http://www.w3.org/ns/anno.jsonld'],
            },
            'id': {
                'type': 'string',
                'format': 'uri',
            },
            'type': {
                'enum': ['Annotation'],
            },
            'created': {
                'type': 'string',
                'format': 'date-time',
            },
            'modified': {
                'type': 'string',
                'format': 'date-time',
            },
            'creator': {
                'type': 'string',
                'format': 'uri',
                'pattern': '^acct:.+$',
            },
            'motivation': {
                'enum': ['commenting', 'replying']
            },
            'body': {
                'type': 'array',
                'minItems': 1,
                'maxItems': 1,
                'items': {
                    'type': 'object',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'enum': ['TextualBody'],
                        },
                        'value': {
                            'type': 'string',
                        },
                        'format': {
                            'type': 'string',
                            'enum': ['text/markdown'],
                        },
                    },
                    'required': [
                        'format',
                        'type',
                        'value',
                    ],
                    'additionalProperties': False,
                },
            },
            'target': {
                'type': 'string',
                'format': 'uri',
            }
        },
        'required': [
            '@context',
            'id',
            'type',
            'created',
            'modified',
            'creator',
            'body',
            'motivation',
            'target',
        ],
        'additionalProperties': False,
    }
