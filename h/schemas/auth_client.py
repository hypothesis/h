# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander

from h import i18n
from h.models.auth_client import GrantType
from h.schemas.base import CSRFSchema, enum_type

_ = i18n.TranslationString
GrantTypeSchemaType = enum_type(GrantType)


class CreateAuthClientSchema(CSRFSchema):
    name = colander.SchemaNode(
             colander.String(),
             title=_('Name'),
             hint=_('This will be displayed to users in the '
                    'authorization prompt'))

    authority = colander.SchemaNode(
                  colander.String(),
                  title=_('Authority'),
                  hint=_('Set of users whose data this client '
                         'can interact with'))

    grant_type = colander.SchemaNode(GrantTypeSchemaType(),
                                     missing=None,
                                     title=_('Grant type'),
                                     hint=_('"authorization_code" or "jwt_bearer"'))

    trusted = colander.SchemaNode(
                colander.Boolean(),
                title=_('Trusted ⚠️'),
                hint=_('Trusted clients do not require user approval. '
                       '⚠️ Only enable this for official Hypothesis clients.'))

    redirect_url = colander.SchemaNode(
                     colander.String(),
                     missing=None,
                     title=_('Redirect URL'),
                     hint=_('The browser will redirect to this URL after '
                            'authorization. Required if grant type is "authorization_code"'))


class EditAuthClientSchema(CreateAuthClientSchema):

    # Read-only fields, listed in the form so that the user can easily copy and
    # paste them into their client's configuration.

    client_id = colander.SchemaNode(
                  colander.String(),
                  title=_('Client ID'))

    client_secret = colander.SchemaNode(
                      colander.String(),
                      missing=None,
                      title=_('Client secret'))
