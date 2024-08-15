from pyramid.request import RequestLocalCache

from h.security.identity import Identity
from h.security.policy.helpers import is_api_request


class BearerTokenPolicy:
    """
    A Bearer token authentication policy.

    This policy uses a bearer token which is validated against Token objects
    in the DB. This can come from the Bearer token header or in the case of
    Websocket requests with the GET parameter `access_token`.

    We use this for our API and Websocket requests.
    """

    def __init__(self):
        self._identity_cache = RequestLocalCache(self._load_identity)

    @staticmethod
    def handles(request) -> bool:
        """Return True if this policy applies to `request`."""
        return is_api_request(request)

    def identity(self, request):
        """
        Get an Identity object for valid credentials.

        Validate the token from the request by matching them to Token records
        in the DB.

        :param request: Pyramid request to inspect
        :returns: An `Identity` object if the login is authenticated or None
        """

        return self._identity_cache.get_or_create(request)

    def _load_identity(self, request):
        token_svc = request.find_service(name="auth_token")
        token_str = None

        # We only ever want to read the access token from GET parameters for
        # websocket requests
        if self._is_ws_request(request):
            token_str = request.GET.get("access_token", None)

        # We currently only accept a real bearer token in our API calls, but
        # it's conceivable the WS spec will one day change to accept this:
        # See: https://github.com/whatwg/html/issues/3062
        if token_str is None:
            token_str = token_svc.get_bearer_token(request)

        if token_str is None:
            return None

        token = token_svc.validate(token_str)
        if token is None:
            return None

        user = request.find_service(name="user").fetch(token.userid)
        if user is None or user.deleted:
            return None

        return Identity.from_models(user=user)

    @staticmethod
    def _is_ws_request(request):
        return request.path == "/ws"
