# -*- coding: utf-8 -*-

from pyramid import authentication
from pyramid import interfaces
from zope import interface

from h.api import auth as api_auth
from h.auth.util import bearer_token
from h.auth.util import effective_principals


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy(object):

    def __init__(self):
        self.session_policy = authentication.SessionAuthenticationPolicy()

    def authenticated_userid(self, request):
        if _is_api_request(request):
            token = bearer_token(request)
            return (api_auth.userid_from_api_token(token) or
                    api_auth.userid_from_jwt(token, request))
        return self.session_policy.authenticated_userid(request)

    def unauthenticated_userid(self, request):
        if _is_api_request(request):
            # We can't always get an unauthenticated userid for an API request,
            # as some of the authentication tokens used may be opaque.
            return self.authenticated_userid(request)
        return self.session_policy.unauthenticated_userid(request)

    def effective_principals(self, request):
        return effective_principals(request.authenticated_userid, request)

    def remember(self, request, userid, **kw):
        if _is_api_request(request):
            return []
        return self.session_policy.remember(request, userid, **kw)

    def forget(self, request):
        if _is_api_request(request):
            return []
        return self.session_policy.forget(request)


def _is_api_request(request):
    return (request.path.startswith('/api') and
            request.path not in ['/api/token', '/api/badge'])
