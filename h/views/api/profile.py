# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPBadRequest

from h import session as h_session
from h.views.api.config import api_config


@api_config(
    route_name="api.profile",
    request_method="GET",
    link_name="profile.read",
    description="Fetch the user's profile",
)
def profile(request):
    authority = request.params.get("authority")
    return h_session.profile(request, authority)


@api_config(
    route_name="api.profile",
    request_method="PATCH",
    permission="update",
    link_name="profile.update",
    description="Update a user's preferences",
)
def update_preferences(request):
    preferences = request.json_body.get("preferences", {})

    svc = request.find_service(name="user")
    # TODO: The following exception doesn't match convention for validation
    # used in other endpoints
    try:
        svc.update_preferences(request.user, **preferences)
    except TypeError as e:
        raise HTTPBadRequest(str(e))

    return h_session.profile(request)
