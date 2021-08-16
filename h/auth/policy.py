import hmac
from typing import Optional

from pyramid import interfaces
from pyramid.authentication import extract_http_basic_credentials
from pyramid.security import Authenticated
from sqlalchemy.exc import StatementError
from zope import interface

from h.exceptions import InvalidUserId
from h.models import AuthClient
from h.models.auth_client import GrantType
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


class IdentityBasedPolicy:
    @classmethod
    def identity(cls, request) -> Optional[Identity]:  # pylint:disable=unused-argument
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
        """
        Return a list of principals for the request.

        If authentication is unsuccessful then the only principal returned is
        `Everyone`

        :param request: Pyramid request to check
        :returns: List of principals
        """
        return principals_for_identity(self.identity(request))

    def remember(self, _request, _userid, **_kwargs):  # pylint: disable=no-self-use
        return []

    def forget(self, _request):  # pylint: disable=no-self-use
        return []


@interface.implementer(interfaces.IAuthenticationPolicy)
class AuthClientPolicy(IdentityBasedPolicy):
    """
    An authentication policy for registered AuthClients.

    Auth clients must be registered with grant type `client_credentials` and
    will need to perform basic HTTP auth with their username and password set
    to their auth client id, and secret.

    A client can also pass an `X-Forwarded-User` header with the userid to
    act as user in their authority. This will create a `request.user` and will
    look like a normal login. This user will have an additional
    principal, `client:{client_id}@{authority}` which lets you tell it apart
    from regular users.
    """

    def unauthenticated_userid(self, request):
        """Return the forwarded userid or the auth_client's id."""

        if forwarded_userid := self._forwarded_userid(request):
            return forwarded_userid

        # Get the username from the basic auth header
        if credentials := extract_http_basic_credentials(request):
            return credentials.username

        return None

    def identity(self, request):
        """
        Get an Identity object for valid credentials.

        :param request: Pyramid request to inspect
        :returns: An `Identity` object if the login is authenticated or None
        """
        # Credentials are required
        auth_client = self._get_auth_client(request)
        if not auth_client:
            return None

        user = None
        if forwarded_userid := self._forwarded_userid(request):
            # If we have a forwarded user it must be valid
            try:
                user = request.find_service(name="user").fetch(forwarded_userid)
            except InvalidUserId:
                return None

            # If you forward a user it must exist and match your authority
            if not user or user.authority != auth_client.authority:
                return None

        return Identity(auth_client=auth_client, user=user)

    @classmethod
    def _get_auth_client(cls, request):
        """Get a matching auth client if the credentials are valid."""

        credentials = extract_http_basic_credentials(request)
        if not credentials:
            return None

        # It is important not to include the secret as part of the SQL query
        # because the resulting code may be subject to a timing attack.
        try:
            auth_client = request.db.query(AuthClient).get(credentials.username)
        except StatementError:
            # The auth client id is malformed
            return None

        if (
            # The client must exist
            auth_client is None
            # Have a secret to compare with
            or auth_client.secret is None
            # And be the correct type
            or auth_client.grant_type != GrantType.client_credentials
        ):
            return None

        # We fetch the auth_client by its ID and then do a constant-time
        # comparison of the secret with that provided in the request.
        if not hmac.compare_digest(auth_client.secret, credentials.password):
            return None

        return auth_client

    @staticmethod
    def _forwarded_userid(request):
        """Return forwarded userid or None."""
        return request.headers.get("X-Forwarded-User", None)


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
    Return if this is auth_client_auth authentication valid for the given request.

    Uuthentication should be performed by
    :py:class:`~h.auth.policy.AuthClientPolicy` only for requests
    that match the whitelist.

    The whitelist will likely evolve.

    :rtype: bool
    """
    if request.matched_route:
        return (request.matched_route.name, request.method) in AUTH_CLIENT_API_WHITELIST
    return False
