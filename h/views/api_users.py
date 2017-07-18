# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import hmac

import sqlalchemy as sa

from h import models
from h.accounts import schemas
from h.auth.util import basic_auth_creds
from h.exceptions import ClientUnauthorized
from h.schemas import ValidationError
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

    schema = schemas.CreateUserAPISchema()
    appstruct = schema.validate(request.json_body)

    _check_authority(client, appstruct)
    appstruct['authority'] = client.authority

    _check_existing_user(request.db, appstruct)

    user_signup_service = request.find_service(name='user_signup')
    user = user_signup_service.signup(require_activation=False, **appstruct)
    return {
        'authority': user.authority,
        'email': user.email,
        'userid': user.userid,
        'username': user.username,
    }


def _check_authority(client, data):
    authority = data.get('authority')
    if client.authority != authority:
        msg = "'authority' does not match authenticated client"
        raise ValidationError(msg)


def _check_existing_user(session, data):
    errors = []

    existing_user = models.User.get_by_email(session,
                                             data['email'],
                                             data['authority'])
    if existing_user:
        errors.append("user with email address %s already exists" % data['email'])

    existing_user = models.User.get_by_username(session,
                                                data['username'],
                                                data['authority'])
    if existing_user:
        errors.append("user with username %s already exists" % data['username'])

    if errors:
        raise ValidationError(', '.join(errors))


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

    if not hmac.compare_digest(client.secret, client_secret):
        raise ClientUnauthorized()

    return client
