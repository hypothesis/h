import hmac

from pyramid.authentication import extract_http_basic_credentials
from sqlalchemy.exc import StatementError

from h.exceptions import InvalidUserId
from h.models import AuthClient
from h.models.auth_client import GrantType
from h.security import Identity
from h.security.policy._identity_base import IdentityBasedPolicy


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

    #: List of route name-method combinations that should
    #: allow AuthClient authentication
    API_WHITELIST = [
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

    @classmethod
    def handles(cls, request):
        """Get whether this policy should accept this request."""

        if request.matched_route:
            return (
                request.matched_route.name,
                request.method,
            ) in cls.API_WHITELIST
        return False

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
        if forwarded_userid := request.headers.get("X-Forwarded-User", None):
            # If we have a forwarded user it must be valid
            try:
                user = request.find_service(name="user").fetch(forwarded_userid)
            except InvalidUserId:
                return None

            # If you forward a user it must exist and match your authority
            if not user or user.authority != auth_client.authority:
                return None

        return Identity.from_models(auth_client=auth_client, user=user)

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
