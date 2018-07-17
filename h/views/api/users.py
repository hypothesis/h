# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import hmac

import sqlalchemy as sa
from pyramid.exceptions import HTTPNotFound

from h import models
from h.auth.util import basic_auth_creds
from h.exceptions import ClientUnauthorized, PayloadError, ConflictError
from h.models.auth_client import GrantType
from h.presenters import UserJSONPresenter
from h.schemas import ValidationError
from h.schemas.api.user import CreateUserAPISchema, UpdateUserAPISchema
from h.services.user_unique import DuplicateUserError
from h.util.view import json_view


@json_view(route_name='api.users', request_method='POST')
def create(request):
    """
    Create a user.

    This API endpoint allows authorised clients (those able to provide a valid
    Client ID and Client Secret) to create users in their authority. These
    users are created pre-activated, and are unable to log in to the web
    service directly.
    """
    client = _request_client(request)

    schema = CreateUserAPISchema()
    appstruct = schema.validate(_json_payload(request))

    _check_authority(client, appstruct)
    appstruct['authority'] = client.authority

    user_unique_service = request.find_service(name='user_unique')

    try:
        user_unique_service.ensure_unique(appstruct, authority=client.authority)
    except DuplicateUserError as err:
        raise ConflictError(err)

    user_signup_service = request.find_service(name='user_signup')
    user = user_signup_service.signup(require_activation=False, **appstruct)
    presenter = UserJSONPresenter(user)
    return presenter.asdict()


@json_view(route_name='api.user', request_method='PATCH')
def update(request):
    """
    Update a user.

    This API endpoint allows authorised clients (those able to provide a valid
    Client ID and Client Secret) to update users in their authority.
    """
    client = _request_client(request)

    user_svc = request.find_service(name='user')
    user = user_svc.fetch(request.matchdict['username'],
                          client.authority)
    if user is None:
        raise HTTPNotFound()

    schema = UpdateUserAPISchema()
    appstruct = schema.validate(_json_payload(request))

    _update_user(user, appstruct)

    presenter = UserJSONPresenter(user)
    return presenter.asdict()


def _check_authority(client, data):
    authority = data.get('authority')
    if client.authority != authority:
        msg = "'authority' does not match authenticated client"
        raise ValidationError(msg)


def _request_client(request):
    creds = basic_auth_creds(request)
    if creds is None:
        raise ClientUnauthorized()

    # We fetch the client by its ID and then do a constant-time comparison of
    # the secret with that provided in the request.
    #
    # It is important not to include the secret as part of the SQL query
    # because the resulting code may be subject to a timing attack.
    client_id, client_secret = creds
    try:
        client = request.db.query(models.AuthClient).get(client_id)
    except sa.exc.StatementError:  # client_id is malformed
        raise ClientUnauthorized()
    if client is None:
        raise ClientUnauthorized()
    if client.secret is None:  # client is not confidential
        raise ClientUnauthorized()
    if client.grant_type != GrantType.client_credentials:  # client not allowed to create users
        raise ClientUnauthorized()

    if not hmac.compare_digest(client.secret, client_secret):
        raise ClientUnauthorized()

    return client


def _update_user(user, appstruct):
    if 'email' in appstruct:
        user.email = appstruct['email']
    if 'display_name' in appstruct:
        user.display_name = appstruct['display_name']


def _json_payload(request):
    try:
        return request.json_body
    except ValueError:
        raise PayloadError()
