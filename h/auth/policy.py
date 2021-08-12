from typing import Optional

from pyramid import interfaces
from pyramid.authentication import extract_http_basic_credentials
from pyramid.security import Authenticated, Everyone
from zope import interface

from h.auth import util
from h.exceptions import InvalidUserId
from h.security import Identity, principals_for_identity

#: List of route name-method combinations that should
#: allow AuthClient authentication
AUTH_CLIENT_API_WHITELIST = [
    ("api.groups", "POST"),
    ("api.group", "PATCH"),
    ("api.group", "GET"),
    ("api.group_upsert", "PUT"),
    ("api.group_member", "POST"),
    ("api.users", "POST"),
    ("api.user_read", "GET"),
    ("api.user", "PATCH"),
    ("api.bulk", "POST"),
]


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthenticationPolicy:
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
class APIAuthenticationPolicy:
    """
    An authentication policy for Hypothesis API endpoints.

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
        Return the request's effective principals.

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
class AuthClientPolicy:
    """
    An authentication policy for registered AuthClients.

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

    def unauthenticated_userid(self, request):
        """
        Return the forwarded userid or the auth_client's id.

        If a forwarded user header is set, return the ``userid`` (its value)
        Otherwise return the username parsed from the Basic Auth header

        :return: :py:attr:`h.models.user.User.userid` or
                 :py:attr:`h.models.auth_client.AuthClient.id`
        :rtype: str
        """
        forwarded_userid = self._forwarded_userid(request)
        if forwarded_userid is not None:
            return forwarded_userid

        # username from BasicAuth header
        credentials = extract_http_basic_credentials(request)
        if credentials:
            return credentials.username

    def authenticated_userid(self, request):
        """
        Return any forwarded userid or None.

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
        forwarded_userid = self._forwarded_userid(request)

        # We require a forwarded user for an authenticated user
        if forwarded_userid is None:
            return None

        # Extract username and password from basic auth header
        credentials = extract_http_basic_credentials(request)
        if not credentials:
            return None

        if self.check(credentials.username, credentials.password, request) is None:
            return None

        # This should always be a userid, not an auth_client id
        return forwarded_userid

    def effective_principals(self, request):
        """
        Return a list of principals for the request.

        If authentication is unsuccessful then the only principal returned is
        `Everyone`

        :param request: Pyramid request to check
        :returns: List of principals
        """
        effective_principals = [Everyone]

        # The parent has this but in our case we do something different?
        # userid = self.unauthenticated_userid(request)
        credentials = extract_http_basic_credentials(request)
        userid = credentials.username
        if userid is None or userid in (Authenticated, Everyone):
            return effective_principals

        groups = self.check(credentials.username, credentials.password, request)
        if groups is None:  # is None!
            return effective_principals

        effective_principals.append(Authenticated)
        effective_principals.append(userid)
        effective_principals.extend(groups)

        return effective_principals

    def remember(self, _request, _userid, **_kwargs):  # pylint: disable=no-self-use
        """Not implemented for basic auth client policy."""
        return []

    def forget(self, _request):  # pylint: disable=no-self-use
        """Not implemented for basic auth client policy."""
        return []

    @staticmethod
    def check(username, password, request):
        """
        Return list of appropriate principals or None if authentication is unsuccessful.

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
        # validate that the credentials in BasicAuth header
        # match an AuthClient record in the db

        client = util.verify_auth_client(
            client_id=username, client_secret=password, db_session=request.db
        )
        user = None

        if client and (forwarded_userid := AuthClientPolicy._forwarded_userid(request)):
            try:
                user = request.find_service(name="user").fetch(forwarded_userid)
            except InvalidUserId:  # raised if userid is invalidly formatted
                return None  # invalid user, so we are failing here

            # If you forward a user it must exist and match your authority
            if not user or user.authority != client.authority:
                return None

        return principals_for_identity(Identity(user=user, auth_client=client))

    @staticmethod
    def _forwarded_userid(request):
        """Return forwarded userid or None."""
        return request.headers.get("X-Forwarded-User", None)


class IdentityBasedPolicy:
    @classmethod
    def identity(cls, request) -> Optional[Identity]:
        """
        Get an Identity object for valid credentials.

        Sub-classes should implement this to return an Identity object when
        the request contains valid credentials.

        :param request: Pyramid request to inspect
        """
        return None

    def authenticated_userid(self, request):
        """
        Return the userid implied by the token in the passed request, if any.

        :param request: Pyramid request to inspect
        :return: The userid authenticated for the passed request or None
        """
        if (identity := self.identity(request)) and identity.user:
            return identity.user.userid

        return None

    def unauthenticated_userid(self, request):  # pylint: disable=no-self-use
        """
        Return the userid implied by the token in the passed request, if any.

        :param request: Pyramid request to inspect
        :return: The userid authenticated for the passed request or None
        """

        # We actually just do the same thing for unauthenticated user ids,
        # which is to say they have to be valid.
        return self.authenticated_userid(request)

    def effective_principals(self, request):
        effective_principals = [Everyone]

        if identity := self.identity(request):
            effective_principals.append(Authenticated)
            effective_principals.append(identity.user.userid)
            effective_principals.extend(principals_for_identity(identity))

        return effective_principals

    def remember(self, _request, _userid, **_kwargs):  # pylint: disable=no-self-use
        return []

    def forget(self, _request):  # pylint: disable=no-self-use
        return []


@interface.implementer(interfaces.IAuthenticationPolicy)
class TokenAuthenticationPolicy(IdentityBasedPolicy):
    """
    A bearer token authentication policy.

    This policy uses a bearer token which is validated against Token objects
    in the DB. This can come from the `request.auth_token` (from
    `h.auth.tokens.auth_token`) or in the case of Websocket requests the
    GET parameter `access_token`.
    """

    def identity(self, request):
        """
        Get an Identity object for valid credentials.

        Validate the token from the request by matching them to Token records
        in the DB.

        :param request: Pyramid request to inspect
        :returns: An `Identity` object if the login is authenticated or None
        """
        token_str = self._get_token(request)
        if token_str is None:
            return None

        token = request.find_service(name="auth_token").validate(token_str)
        if token is None:
            return None

        user = request.find_service(name="user").fetch(token.userid)
        if user is None:
            return None

        return Identity(user=user)

    def _get_token(self, request):
        token_str = None

        if self._is_ws_request(request):
            token_str = request.GET.get("access_token", None)

        return token_str or getattr(request, "auth_token", None)

    @staticmethod
    def _is_ws_request(request):
        return request.path == "/ws"


@interface.implementer(interfaces.IAuthenticationPolicy)
class RemoteUserAuthenticationPolicy(IdentityBasedPolicy):
    """An authentication policy which blindly trusts a header."""

    def unauthenticated_userid(self, request):
        return request.environ.get("HTTP_X_FORWARDED_USER")

    def identity(self, request):
        user_id = self.unauthenticated_userid(request)
        if not user_id:
            return None

        user = request.find_service(name="user").fetch(user_id)
        if user is None:
            return None

        return Identity(user=user)


def _is_api_request(request):
    return request.path.startswith("/api") and request.path not in [
        "/api/token",
        "/api/badge",
    ]


def _is_client_request(request):
    """
    Return if this is client_auth authentication valid for the given request.

    Uuthentication should be performed by
    :py:class:`~h.auth.policy.AuthClientPolicy` only for requests
    that match the whitelist.

    The whitelist will likely evolve.

    :rtype: bool
    """
    if request.matched_route:
        return (request.matched_route.name, request.method) in AUTH_CLIENT_API_WHITELIST
    return False
