from pyramid.interfaces import ISecurityPolicy
from pyramid.request import RequestLocalCache
from zope.interface import implementer

from h.security import Identity
from h.security.policy._identity_base import IdentityBasedPolicy


class BearerTokenPolicy(IdentityBasedPolicy):
    """
    A Bearer token authentication policy.

    This policy uses a Bearer token header which is validated against Token
    objects in the DB.
    """

    def __init__(self):
        self._identity_cache = RequestLocalCache(self._load_identity)

    def identity(self, request):
        """
        Get an Identity object for valid credentials.

        Validate the token from the request by matching them to Token records
        in the DB.

        :param request: Pyramid request to inspect
        :returns: An `Identity` object if the login is authenticated or None
        """

        return self._identity_cache.get_or_create(request)

    @classmethod
    def get_token_string(cls, request):
        """Get the token from a request."""

        # This is a customisation point which is used in
        # `h.streamer.security.AccessTokenPolicy`
        return request.find_service(name="auth_token").get_bearer_token(request)

    def _load_identity(self, request):
        token_str = self.get_token_string(request)
        if token_str is None:
            return None

        token = request.find_service(name="auth_token").validate(token_str)
        if token is None:
            return None

        user = request.find_service(name="user").fetch(token.userid)
        if user is None:
            return None

        return Identity.from_models(user=user)
