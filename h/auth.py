"""Our authentication policy."""

import logging

import jwt
from pyramid import authentication
from pyramid import interfaces
from pyramid import security
from zope import interface

from h import accounts
from h.api import auth
from h.api import groups


log = logging.getLogger(__name__)


JWT_BEARER = 'urn:ietf:params:oauth:grant-type:jwt-bearer'


LEEWAY = 240  # Allowance for clock skew in verification.


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy(object):

    def __init__(self):
        self.session_policy = authentication.SessionAuthenticationPolicy()

    def authenticated_userid(self, request):
        if is_api_request(request):
            return userid_from_jwt(request)
        return self.session_policy.authenticated_userid(request)

    def unauthenticated_userid(self, request):
        if is_api_request(request):
            # We can't always get an unauthenticated userid for an API request,
            # as some of the authentication tokens used may be opaque.
            return self.authenticated_userid(request)
        return self.session_policy.unauthenticated_userid(request)

    def effective_principals(self, request):
        return effective_principals(request.authenticated_userid, request)

    def remember(self, request, userid, **kw):
        if is_api_request(request):
            return []
        return self.session_policy.remember(request, userid, **kw)

    def forget(self, request):
        if is_api_request(request):
            return []
        return self.session_policy.forget(request)


def auth_domain(request):
    """Return the value of the h.auth_domain config settings.

    Falls back on returning request.domain if h.auth_domain isn't set.

    """
    return request.registry.settings.get('h.auth_domain', request.domain)


def groupfinder(userid, request):
    """
    Return the list of additional groups of which userid is a member.

    Returns a list of group principals of which the passed userid is a member,
    or None if the userid is not known by this application.
    """
    principals = set()

    user = accounts.get_user(userid, request)
    if user is None:
        return

    if user.admin:
        principals.add('group:__admin__')
    if user.staff:
        principals.add('group:__staff__')
    principals.update(groups.group_principals(user))

    return list(principals)


def effective_principals(userid, request, groupfinder=groupfinder):
    """
    Return the list of effective principals for the passed userid.

    Usually, we can leave the computation of the full set of effective
    principals to the pyramid authentication policy. Sometimes, however, it can
    be useful to discover the full set of effective principals for a userid
    other than the current authenticated userid. This function replicates the
    normal behaviour of a pyramid authentication policy and can be used for
    that purpose.
    """
    principals = set([security.Everyone])

    groups = groupfinder(userid, request)
    if groups is not None:
        principals.add(security.Authenticated)
        principals.add(userid)
        principals.update(groups_)

    return list(principals)


def is_api_request(request):
    return (request.path.startswith('/api') and
            request.path not in ['/api/token', '/api/badge'])


def userid_from_jwt(request):
    if 'Authorization' not in request.headers:
        return None
    token = request.headers.get('Authorization')[7:]
    return validate_bearer_token(token, request)


def validate_bearer_token(token, request):
    if token is None:
        return None

    try:
        payload = jwt.decode(token, verify=False)
    except jwt.InvalidTokenError:
        return False

    aud = request.host_url
    iss = payload['iss']
    sub = payload.get('sub')

    try:
        payload = jwt.decode(token,
                             key=request.registry.settings['h.client_secret'],
                             audience=aud,
                             leeway=LEEWAY,
                             algorithms=['HS256'])

    except jwt.InvalidTokenError:
        return None

    return sub


def includeme(config):
    # Allow retrieval of the auth_domain from the request object.
    config.add_request_method(auth_domain, name='auth_domain', reify=True)
