# -*- coding: utf-8 -*-

from pyramid import authentication
from pyramid import interfaces
from zope import interface

from h.auth import tokens
from h.auth import util


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy(object):

    def __init__(self):
        self.session_policy = authentication.SessionAuthenticationPolicy()

    def authenticated_userid(self, request):
        if _is_api_request(request):
            return tokens.authenticated_userid(request)
        return self.session_policy.authenticated_userid(request)

    def unauthenticated_userid(self, request):
        if _is_api_request(request):
            # We can't really get an "unauthenticated" userid for an API
            # request. We have to actually go and decode/look up the tokens and
            # get what is effectively an authenticated userid.
            return tokens.authenticated_userid(request)
        return self.session_policy.unauthenticated_userid(request)

    def effective_principals(self, request):
        return util.effective_principals(request.authenticated_userid, request)

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
