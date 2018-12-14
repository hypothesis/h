# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.auth.util import client_authority
from h.exceptions import PayloadError, ConflictError
from h.presenters import UserJSONPresenter
from h.schemas.api.user import CreateUserAPISchema, UpdateUserAPISchema
from h.schemas import ValidationError
from h.services.user_unique import DuplicateUserError
from h.util.view import json_view


@json_view(route_name="api.users", request_method="POST", permission="create")
def create(request):
    """
    Create a user.

    This API endpoint allows authorised clients (those able to provide a valid
    Client ID and Client Secret) to create users in their authority. These
    users are created pre-activated, and are unable to log in to the web
    service directly.

    Note: the authority-enforcement logic herein is, by necessity, strange.
    The API accepts an ``authority`` parameter but the only valid value for
    the param is the client's verified authority. If the param does not
    match the client's authority, ``ValidationError`` is raised.

    :raises ValidationError: if ``authority`` param does not match client
                             authority
    :raises ConflictError:   if user already exists
    """
    client_authority_ = client_authority(request)
    schema = CreateUserAPISchema()
    appstruct = schema.validate(_json_payload(request))

    # Enforce authority match
    if appstruct["authority"] != client_authority_:
        raise ValidationError(
            "authority '{auth_param}' does not match client authority".format(
                auth_param=appstruct["authority"]
            )
        )

    user_unique_service = request.find_service(name="user_unique")

    try:
        user_unique_service.ensure_unique(appstruct, authority=client_authority_)
    except DuplicateUserError as err:
        raise ConflictError(str(err))

    user_signup_service = request.find_service(name="user_signup")
    user = user_signup_service.signup(require_activation=False, **appstruct)
    presenter = UserJSONPresenter(user)
    return presenter.asdict()


@json_view(route_name="api.user", request_method="PATCH", permission="update")
def update(user, request):
    """
    Update a user.

    This API endpoint allows authorised clients (those able to provide a valid
    Client ID and Client Secret) to update users in their authority.
    """
    schema = UpdateUserAPISchema()
    appstruct = schema.validate(_json_payload(request))

    user_update_service = request.find_service(name="user_update")
    user = user_update_service.update(user, **appstruct)

    presenter = UserJSONPresenter(user)
    return presenter.asdict()


def _json_payload(request):
    try:
        return request.json_body
    except ValueError:
        raise PayloadError()
