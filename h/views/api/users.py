# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.exceptions import HTTPNotFound

from h.auth.util import request_auth_client, client_authority
from h.exceptions import PayloadError, ConflictError
from h.presenters import UserJSONPresenter
from h.schemas.api.user import CreateUserAPISchema, UpdateUserAPISchema
from h.services.user_unique import DuplicateUserError
from h.util.view import json_view


@json_view(route_name='api.users',
           request_method='POST',
           permission='create')
def create(request):
    """
    Create a user.

    This API endpoint allows authorised clients (those able to provide a valid
    Client ID and Client Secret) to create users in their authority. These
    users are created pre-activated, and are unable to log in to the web
    service directly.
    """
    applied_authority = client_authority(request)
    schema = CreateUserAPISchema()
    appstruct = schema.validate(_json_payload(request))

    # Enforce authority match to currently-active auth-client authority
    appstruct['authority'] = applied_authority

    user_unique_service = request.find_service(name='user_unique')

    try:
        user_unique_service.ensure_unique(appstruct, authority=applied_authority)
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
    client = request_auth_client(request)

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
