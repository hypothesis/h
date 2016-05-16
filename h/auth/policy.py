# -*- coding: utf-8 -*-

from pyramid import authentication
from pyramid import interfaces
from zope import interface

from h import accounts
from h.auth import tokens
from h.auth import util


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy(object):

    def __init__(self):
        self.session_policy = authentication.SessionAuthenticationPolicy()

    def authenticated_userid(self, request):
        authenticated_userid = None

        if _is_api_request(request):
            authenticated_userid = tokens.authenticated_userid(request)
        else:
            authenticated_userid = self.session_policy.authenticated_userid(
                request)

        # If the user account has been deleted from the database then log the
        # user out.
        if not accounts.get_user(authenticated_userid, request):
            self.forget(request)
            return None

        return authenticated_userid

    def unauthenticated_userid(self, request):
        unauthenticated_userid = None

        if _is_api_request(request):
            # We can't really get an "unauthenticated" userid for an API
            # request. We have to actually go and decode/look up the tokens and
            # get what is effectively an authenticated userid.
            unauthenticated_userid = tokens.authenticated_userid(request)
        else:
            unauthenticated_userid = (
                self.session_policy.unauthenticated_userid(request))

        # If the user account has been deleted from the database then log the
        # user out.
        if not accounts.get_user(unauthenticated_userid, request):
            self.forget(request)
            return None

        return unauthenticated_userid

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
