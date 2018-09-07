# -*- coding: utf-8 -*-
"""Classes for validating data passed to the annotations API."""
from __future__ import unicode_literals

import colander
import copy
from pyramid import i18n

from h.schemas.base import JSONSchema, ValidationError
from h.search.query import LIMIT_DEFAULT, LIMIT_MAX, OFFSET_MAX
from h.util import document_claims

_ = i18n.TranslationStringFactory(__package__)


class AnnotationSchema(JSONSchema):

    """Validate an annotation object."""

    schema = {
        'type': 'object',
        'properties': {
            'document': {
                'type': 'object',
                'properties': {
                    'dc': {
                        'type': 'object',
                        'properties': {
                            'identifier': {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                },
                            },
                        },
                    },
                    'highwire': {
                        'type': 'object',
                        'properties': {
                            'doi': {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                },
                            },
                            'pdf_url': {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                },
                            },
                        },
                    },
                    'link': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'href': {
                                    'type': 'string',
                                },
                                'type': {
                                    'type': 'string',
                                },
                            },
                            'required': [
                                'href',
                            ],
                        },
                    },
                },
            },
            'group': {
                'type': 'string',
            },
            'permissions': {
                'title': 'Permissions',
                'description': 'Annotation action access control list',
                'type': 'object',
                'patternProperties': {
                    '^(admin|delete|read|update)$': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'pattern': '^(acct:|group:).+$',
                        },
                    }
                },
                'required': [
                    'read',
                ],
            },
            'references': {
                'type': 'array',
                'items': {
                    'type': 'string',
                },
            },
            'tags': {
                'type': 'array',
                'items': {
                    'type': 'string',
                },
            },
            'target': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'selector': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'type': {'type': 'string'}
                                },
                                'required': ['type']
                            }
                        },
                    },
                },
            },
            'text': {
                'type': 'string',
            },
            'uri': {
                'type': 'string',
            },
        },
    }


class CreateAnnotationSchema(object):

    """Validate the POSTed data of a create annotation request."""

    def __init__(self, request):
        self.structure = AnnotationSchema()
        self.request = request

    def validate(self, data):
        appstruct = self.structure.validate(data)

        new_appstruct = {}

        _remove_protected_fields(appstruct)

        new_appstruct['userid'] = self.request.authenticated_userid

        uri = appstruct.pop('uri', '').strip()
        if not uri:
            raise ValidationError('uri: ' + _("'uri' is a required property"))
        new_appstruct['target_uri'] = uri

        new_appstruct['text'] = appstruct.pop('text', '')
        new_appstruct['tags'] = appstruct.pop('tags', [])
        new_appstruct['groupid'] = appstruct.pop('group', '__world__')
        new_appstruct['references'] = appstruct.pop('references', [])

        if 'permissions' in appstruct:
            new_appstruct['shared'] = _shared(appstruct.pop('permissions'),
                                              new_appstruct['groupid'])
        else:
            new_appstruct['shared'] = False

        if 'target' in appstruct:
            new_appstruct['target_selectors'] = _target_selectors(
                appstruct.pop('target'))

        # Replies always get the same groupid as their parent. The parent's
        # groupid is added to the reply annotation later by the storage code.
        # Here we just delete any group sent by the client from replies.
        if new_appstruct['references'] and 'groupid' in new_appstruct:
            del new_appstruct['groupid']

        new_appstruct['document'] = _document(appstruct.pop('document', {}),
                                              new_appstruct['target_uri'])

        new_appstruct['extra'] = appstruct

        return new_appstruct


class UpdateAnnotationSchema(object):

    """Validate the POSTed data of an update annotation request."""

    def __init__(self, request, existing_target_uri, groupid):
        self.request = request
        self.existing_target_uri = existing_target_uri
        self.groupid = groupid
        self.structure = AnnotationSchema()

    def validate(self, data):
        appstruct = self.structure.validate(data)

        new_appstruct = {}

        _remove_protected_fields(appstruct)

        # Some fields are not allowed to be changed in annotation updates.
        for key in ['group', 'groupid', 'userid', 'references']:
            appstruct.pop(key, '')

        # Fields that are allowed to be updated and that have a different name
        # internally than in the public API.
        if 'uri' in appstruct:
            new_uri = appstruct.pop('uri').strip()
            if not new_uri:
                raise ValidationError(
                    'uri: ' + _("'uri' is a required property"))
            new_appstruct['target_uri'] = new_uri

        if 'permissions' in appstruct:
            new_appstruct['shared'] = _shared(appstruct.pop('permissions'),
                                              self.groupid)

        if 'target' in appstruct:
            new_appstruct['target_selectors'] = _target_selectors(
                appstruct.pop('target'))

        # Fields that are allowed to be updated and that have the same internal
        # and external name.
        for key in ['text', 'tags']:
            if key in appstruct:
                new_appstruct[key] = appstruct.pop(key)

        if 'document' in appstruct:
            new_appstruct['document'] = _document(
                appstruct.pop('document'),
                new_appstruct.get('target_uri', self.existing_target_uri))

        new_appstruct['extra'] = appstruct

        return new_appstruct


def _document(document, claimant):
    """
    Return document meta and document URI data from the given document dict.

    Transforms the "document" dict that the client posts into a convenient
    format for creating DocumentURI and DocumentMeta objects later.

    """
    document = document or {}
    document_uri_dicts = document_claims.document_uris_from_data(
        copy.deepcopy(document),
        claimant=claimant)
    document_meta_dicts = document_claims.document_metas_from_data(
        copy.deepcopy(document),
        claimant=claimant)
    return {
        'document_uri_dicts': document_uri_dicts,
        'document_meta_dicts': document_meta_dicts
    }


def _format_jsonschema_error(error):
    """Format a :py:class:`jsonschema.ValidationError` as a string."""
    if error.path:
        dotted_path = '.'.join([str(c) for c in error.path])
        return '{path}: {message}'.format(path=dotted_path,
                                          message=error.message)
    return error.message


def _remove_protected_fields(appstruct):
    # Some fields are not to be set by the user, ignore them.
    for field in ['created',
                  'updated',
                  'user',
                  'id',
                  'links',
                  'flagged',
                  'hidden',
                  'moderation',
                  'user_info']:
        appstruct.pop(field, None)


def _shared(permissions, groupid):
    """
    Return True if the given permissions object represents shared permissions.

    Return False otherwise.

    Reduces the client's complex permissions dict to a simple shared boolean.

    :param permissions: the permissions dict sent by the client in an
        annotation create or update request
    :type permissions: dict

    :param groupid: the groupid of the annotation that the permissions dict
        applies to
    :type groupid: unicode

    """
    return permissions['read'] == ['group:{id}'.format(id=groupid)]


def _target_selectors(targets):
    """
    Return the target selectors from the given target list.

    Transforms the target lists that the client sends in annotation create and
    update requests into our internal target_selectors format.

    """
    # Any targets other than the first in the list are discarded.
    # Any fields of the target other than 'selector' are discarded.
    if targets and 'selector' in targets[0]:
        return targets[0]['selector']
    else:
        return []


class SearchParamsSchema(colander.Schema):
    _separate_replies = colander.SchemaNode(
        colander.Boolean(),
        missing=False,
        description="Return a separate set of annotations and their replies.",
    )
    sort = colander.SchemaNode(
        colander.String(),
        validator=colander.OneOf(["created", "updated", "group", "id", "user"]),
        missing="updated",
        description="The field by which annotations should be sorted.",
    )
    limit = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=LIMIT_MAX),
        missing=LIMIT_DEFAULT,
        description="The maximum number of annotations to return.",
    )
    order = colander.SchemaNode(
        colander.String(),
        validator=colander.OneOf(["asc", "desc"]),
        missing="desc",
        description="The direction of sort.",
    )
    offset = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=OFFSET_MAX),
        missing=0,
        description="""The number of initial annotations to skip. This is
                       used for pagination.""",
    )
    group = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="Limit the results to this group of annotations.",
    )
    quote = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Limit the results to annotations that contain this text inside
                        the text that was annotated.""",
    )
    references = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Returns annotations that are replies to this parent annotation id.""",
    )
    tag = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Limit the results to annotations tagged with the specified value.",
    )
    tags = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Alias of tag.",
    )
    text = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Limit the results to annotations that contain this text in their textual body.",
    )
    uri = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Limit the results to annotations matching the specific URI
                       or equivalent URIs. URI can be a URL (a web page address) or
                       a URN representing another kind of resource such as DOI
                       (Digital Object Identifier) or a PDF fingerprint.""",
    )
    uri_parts = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        name='uri.parts',
        missing=colander.drop,
        description="""Limit the results to annotations with the given keywords
                       appearing in the URL.""",
    )
    url = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Alias of uri.",
    )
    any = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Limit the results to annotations whose quote, tags,
                       text or url fields contain this keyword.""",
    )
    user = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="Limit the results to annotations made by the specified user.",
    )
