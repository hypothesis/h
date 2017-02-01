# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from h import session as h_session
from memex.views import api_config


@api_config(route_name='api.profile',
            request_method='GET',
            effective_principals=security.Authenticated,
            link_name='profile.read',
            description="Fetch the user's profile")
def profile(request):
    return h_session.profile(request)
