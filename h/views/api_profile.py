# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from h import session as h_session
from h.exceptions import APIError
from h.views.api_config import api_config


@api_config(route_name='api.profile',
            request_method='GET',
            link_name='profile.read',
            description="Fetch the user's profile")
def profile(request):
    authority = request.params.get('authority')
    return h_session.profile(request, authority)


@api_config(route_name='api.profile',
            request_method='PATCH',
            effective_principals=security.Authenticated,
            link_name='profile.update',
            description="Update a user's preferences")
def update_preferences(request):
    preferences = request.json_body.get('preferences', {})

    svc = request.find_service(name='user')
    try:
        svc.update_preferences(request.user, **preferences)
    except TypeError as e:
        raise APIError(e.message, status_code=400)

    return h_session.profile(request)
