from pyramid.httpexceptions import HTTPConflict

from h.presenters import TrustedUserJSONPresenter
from h.schemas import ValidationError
from h.schemas.api.user import CreateUserAPISchema, UpdateUserAPISchema
from h.security import Permission
from h.services.user_unique import DuplicateUserError
from h.views.api.config import api_config
from h.views.api.exceptions import PayloadError


@api_config(
    versions=["v1", "v2"],
    route_name="api.user_read",
    request_method="GET",
    link_name="user.read",
    description="Fetch a user",
    permission=Permission.User.READ,
)
def read(context, _request):
    """
    Fetch a user.

    This API endpoint allows authorized clients (those able to provide a valid
    Client ID and Client Secret) to read users in their authority.
    """
    return TrustedUserJSONPresenter(context.user).asdict()


@api_config(
    versions=["v1", "v2"],
    route_name="api.users",
    request_method="POST",
    link_name="user.create",
    description="Create a new user",
    permission=Permission.User.CREATE,
)
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
    :raises HTTPConflict:    if user already exists
    """
    appstruct = CreateUserAPISchema().validate(_json_payload(request))

    # Enforce authority match
    client_authority = request.identity.auth_client.authority
    if appstruct["authority"] != client_authority:
        raise ValidationError(
            f"""authority '{appstruct["authority"]}' does not match client authority"""
        )

    user_unique_service = request.find_service(name="user_unique")
    try:
        user_unique_service.ensure_unique(appstruct, authority=client_authority)
    except DuplicateUserError as err:
        raise HTTPConflict(str(err)) from err

    user = request.find_service(name="user_signup").signup(
        require_activation=False, **appstruct
    )

    return TrustedUserJSONPresenter(user).asdict()


@api_config(
    versions=["v1", "v2"],
    route_name="api.user",
    request_method="PATCH",
    link_name="user.update",
    description="Update a user",
    permission=Permission.User.UPDATE,
)
def update(context, request):
    """
    Update a user.

    This API endpoint allows authorised clients (those able to provide a valid
    Client ID and Client Secret) to update users in their authority.
    """
    appstruct = UpdateUserAPISchema().validate(_json_payload(request))

    user = request.find_service(name="user_update").update(context.user, **appstruct)

    return TrustedUserJSONPresenter(user).asdict()


def _json_payload(request):
    try:
        return request.json_body
    except ValueError as err:
        raise PayloadError() from err
