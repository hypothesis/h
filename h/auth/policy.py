# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pyramid.compat
from pyramid import interfaces
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.security import Authenticated
from zope import interface

from h.auth import util

#: List of route name-method combinations that should
#: allow AuthClient authentication
AUTH_CLIENT_API_WHITELIST = [
    ('api.groups', 'POST'),
    ('api.group', 'PATCH'),
    ('api.group_upsert', 'PUT'),
    ('api.group_member', 'POST'),
    ('api.users', 'POST'),
    ('api.user', 'PATCH'),
]


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy(object):
    def __init__(self, api_policy, fallback_policy):
        self.api_policy = api_policy
        self.fallback_policy = fallback_policy

    def authenticated_userid(self, request):
        if _is_api_request(request):
            return self.api_policy.authenticated_userid(request)

        return self.fallback_policy.authenticated_userid(request)

    def unauthenticated_userid(self, request):
        if _is_api_request(request):
            return self.api_policy.unauthenticated_userid(request)
        return self.fallback_policy.unauthenticated_userid(request)

    def effective_principals(self, request):
        if _is_api_request(request):
            return self.api_policy.effective_principals(request)
        return self.fallback_policy.effective_principals(request)

    def remember(self, request, userid, **kw):
        if _is_api_request(request):
            return self.api_policy.remember(request, userid, **kw)
        return self.fallback_policy.remember(request, userid, **kw)

    def forget(self, request):
        if _is_api_request(request):
            return self.api_policy.forget(request)
        return self.fallback_policy.forget(request)


@interface.implementer(interfaces.IAuthenticationPolicy)
class APIAuthenticationPolicy(object):
    """
    An authentication policy for Hypothesis API endpoints

    Two types of authentication apply to Hypothesis API endpoints:

    * Authentication for a single user using Token authentication
    * Authentication for an auth_client, either as the client itself or
      "on behalf of" a user within that client's authority

    This policy delegates to :py:class:`~h.auth.TokenAuthenticationPolicy` and
    :py:class:`~h.auth.AuthClientPolicy`, always preferring Token when available

    Initially, the ``client_policy`` will only be used to authenticate requests
    that correspond to certain endpoint services.
    """
    def __init__(self, user_policy, client_policy):
        self._user_policy = user_policy
        self._client_policy = client_policy

    def authenticated_userid(self, request):
        user_authid = self._user_policy.authenticated_userid(request)
        if user_authid is None and _is_client_request(request):
            return self._client_policy.authenticated_userid(request)
        return user_authid

    def unauthenticated_userid(self, request):
        user_unauth_id = self._user_policy.unauthenticated_userid(request)
        if user_unauth_id is None and _is_client_request(request):
            return self._client_policy.unauthenticated_userid(request)
        return user_unauth_id

    def effective_principals(self, request):
        """
        Return the request's effective principals

        The ``effective_principals`` method of classes that implement
        Pyramid's Authentication Interface always returns at least one principal:
        :py:attr:`pyramid.security.Everyone`

        The absence of :py:attr:`pyramid.security.Authenticated` in returned
        principals means that authentication was not successful on this request
        using the given policy.

        :rtype: list Containing at minimum :py:attr:`pyramid.security.Everyone`
        """
        user_principals = self._user_policy.effective_principals(request)
        # If authentication via user_policy was not successful
        if Authenticated not in user_principals and _is_client_request(request):
            return self._client_policy.effective_principals(request)
        return user_principals

    def remember(self, request, userid, **kw):
        remembered = self._user_policy.remember(request, userid, **kw)
        if remembered == [] and _is_client_request(request):
            return self._client_policy.remember(request, userid, **kw)
        return remembered

    def forget(self, request):
        forgot = self._user_policy.forget(request)
        if forgot == [] and _is_client_request(request):
            return self._client_policy.forget(request)
        return forgot


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthClientPolicy(object):

    """
    An authentication policy for registered AuthClients

    Authentication for a request to API routes with HTTP Basic Authentication
    credentials that represent a registered AuthClient with
    grant type of ``client_credentials`` in the db.

    Authentication can be of two types:

    * The client itself:

      Some endpoints allow an authenticated auth_client to
      take action on users within its authority, such as creating a user or
      adding a user to a group. In this case, assuming credentials are valid,
      the request will be authenticated, but no ``authenticated_userid`` (and
      thus no request.user) will be set

    * A user within the client's associated authority:

      If an HTTP
      ``X-Forwarded-User`` header is present, its value will be treated as a
      ``userid`` and, if the client credentials are valid _and_ the userid
      represents an extant user within the client's authority, the request
      will be authenticated as that user. In this case, ``authenticated_userid``
      will be set and there will ultimately be a request.user available.

    Note: To differentiate between request with a Token-authenticated user and
    a request with an auth_client forwarded user, the latter has an additional
    principal, ``client:{client_id}@{authority}`` to mark it as being authenticated
    on behalf of an auth_client
    """

    def __init__(self, check=None):
        if check is None:
            check = AuthClientPolicy.check
        self._basic_auth_policy = BasicAuthAuthenticationPolicy(check=check)

    def unauthenticated_userid(self, request):
        """
        Return the forwarded userid or the auth_client's id

        If a forwarded user header is set, return the ``userid`` (its value)
        Otherwise return the username parsed from the Basic Auth header

        :return: :py:attr:`h.models.user.User.userid` or
                 :py:attr:`h.models.auth_client.AuthClient.id`
        :rtype: str
        """
        forwarded_userid = AuthClientPolicy._forwarded_userid(request)
        if forwarded_userid is not None:
            return forwarded_userid

        # username from BasicAuth header
        return self._basic_auth_policy.unauthenticated_userid(request)

    def authenticated_userid(self, request):
        """
        Return any forwarded userid or None

        Rely mostly on
        :py:meth:`pyramid.authentication.BasicAuthAuthenticationPolicy.authenticated_userid`,
        but don't actually return a ``userid`` unless there is a forwarded user
        header set—the auth client itself is not a "user"

        Although this looks as if it trusts the return value of
        :py:meth:`pyramid.authentication.BasicAuthAuthenticationPolicy.authenticated_userid`
        irrationally, rest assured that :py:meth:`~h.auth.policy.AuthClientPolicy.check`
        will always be called (via
        :py:meth:`pyramid.authentication.BasicAuthAuthenticationPolicy.callback`)
        before any non-None value is returned.

        :rtype: :py:attr:`h.models.user.User.userid` or ``None``
        """
        forwarded_userid = AuthClientPolicy._forwarded_userid(request)

        # only evaluate setting an authenticated_userid if forwarded user is present
        if forwarded_userid is None:
            return None

        # username extracted from BasicAuth header
        auth_userid = self._basic_auth_policy.unauthenticated_userid(request)

        # authentication of BasicAuth and forwarded user—this will invoke check
        callback_ok = self._basic_auth_policy.callback(auth_userid, request)

        if callback_ok is not None:
            return forwarded_userid  # This should always be a userid, not an auth_client id

    def effective_principals(self, request):
        """
        Return a list of principals for the request

        This will concatenate the principals returned by
        :py:meth:`~h.auth.policy.AuthClientPolicy.check`
        (which is a list or None) with Pyramid's system principal(s).

        If :py:meth:`~h.auth.policy.AuthClientPolicy.check` returns None—that is,
        if authentication is unsuccessful—the returned principals will only
        contain Pyramid's ``system.Everyone`` principal
        (and Pyramid will not consider the request as authenticated).

        :rtype: list ``['system.Everyone']`` concatenated with any principals
                from a successful authentication
        """
        return self._basic_auth_policy.effective_principals(request)

    def remember(self, request, userid, **kw):
        """Not implemented for basic auth client policy."""
        return []

    def forget(self, request):
        """Not implemented for basic auth client policy."""
        return []

    @staticmethod
    def check(username, password, request):
        """
        Return list of appropriate principals or None if authentication is
        unsuccessful.

        Validate the basic auth credentials from the request by matching them to
        an auth_client record in the DB.

        If an HTTP ``X-Forwarded-User`` header is present in the request, this
        represents the intent to authenticate "on behalf of" a user within
        the auth_client's authority. If this header is present, the user indicated
        by its value (a :py:attr:`h.models.user.User.userid`) _must_ exist and
        be within the auth_client's authority, or authentication will fail.

        :param username: username parsed out of Authorization header (Basic)
        :param password: password parsed out of Authorization header (Basic)
        :returns: additional principals for the auth_client or None
        :rtype: list or None
        """
        client_id = username
        client_secret = password

        # validate that the credentials in BasicAuth header
        # match an AuthClient record in the db
        client = util.verify_auth_client(client_id, client_secret, request.db)

        if client is None:
            return None

        forwarded_userid = AuthClientPolicy._forwarded_userid(request)

        if forwarded_userid is None:  # No forwarded user; set principals for basic auth_client
            return util.principals_for_auth_client(client)

        user_service = request.find_service(name='user')
        try:
            user = user_service.fetch(forwarded_userid)
        except ValueError:  # raised if userid is invalid format
            return None  # invalid user, so we are failing here

        if user and user.authority == client.authority:
            return util.principals_for_auth_client_user(user, client)

        return None

    @staticmethod
    def _forwarded_userid(request):
        """Return forwarded userid or None"""
        userid = request.headers.get('X-Forwarded-User', None)
        if userid is not None:
            # In Python 2 request header values are byte strings, so we need to
            # decode them to get unicode.
            # FIXME: Remove this once we've moved to Python 3.
            userid = pyramid.compat.text_(userid)
        return userid


@interface.implementer(interfaces.IAuthenticationPolicy)
class TokenAuthenticationPolicy(CallbackAuthenticationPolicy):

    """
    A bearer token authentication policy.

    This is a Pyramid authentication policy in which the user's identity is
    provided by and authenticated by the presence of a valid authentication
    token associated with the request. The token is retrieved from the
    ``request.auth_token`` property, which is provided by the
    :py:func:`h.auth.token.auth_token` function.

    It uses Pyramid's CallbackAuthenticationPolicy to divide responsibility
    between this component (which is responsible only for establishing
    identity), and a callback function, which is responsible for providing
    additional principals for the authenticated user.
    """

    def __init__(self, callback=None, debug=False):
        self.callback = callback
        self.debug = debug

    def remember(self, request, userid, **kw):
        """Not implemented for token auth policy."""
        return []

    def forget(self, request):
        """Not implemented for token auth policy."""
        return []

    def unauthenticated_userid(self, request):
        """
        Return the userid implied by the token in the passed request, if any.

        :param request: a request object
        :type request: pyramid.request.Request

        :returns: the userid authenticated for the passed request or None
        :rtype: unicode or None
        """
        token_str = None
        if _is_ws_request(request):
            token_str = request.GET.get('access_token', None)
        if token_str is None:
            token_str = getattr(request, 'auth_token', None)

        if token_str is None:
            return None

        svc = request.find_service(name='auth_token')
        token = svc.validate(token_str)
        if token is None:
            return None

        return token.userid


def _is_api_request(request):
    return (request.path.startswith('/api')
            and request.path not in ['/api/token', '/api/badge'])


def _is_client_request(request):
    """
    Is client_auth authentication valid for the given request?

    Uuthentication should be performed by
    :py:class:`~h.auth.policy.AuthClientPolicy` only for requests
    that match the whitelist.

    The whitelist will likely evolve.

    :rtype: bool
    """
    if request.matched_route:
        return (request.matched_route.name, request.method) in AUTH_CLIENT_API_WHITELIST
    return False


def _is_ws_request(request):
    return request.path == '/ws'
