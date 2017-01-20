# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from h import session as h_session
from h.util.view import json_view


@json_view(route_name='api.profile',
           request_method='GET',
           effective_principals=security.Authenticated)
def profile(request):
    return h_session.profile(request)
