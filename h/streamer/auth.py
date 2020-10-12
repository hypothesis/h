from contextlib import contextmanager

from h.auth import TokenAuthenticationPolicy
from h.auth.util import groupfinder


class AuthenticationPolicy(TokenAuthenticationPolicy):
    def unauthenticated_userid(self, request):
        """
        Return the userid implied by the token in the passed request, if any.

        :param request: a request object
        :type request: pyramid.request.Request

        :returns: the userid authenticated for the passed request or None
        :rtype: unicode or None
        """

        websocket_userid = getattr(request, "websocket_userid", None)
        if websocket_userid is not None:
            return websocket_userid

        token_str = request.GET.get("access_token", None)

        if token_str is None:
            return super().unauthenticated_userid(request)

        return self._userid_for_token(request, token_str)


POLICY = AuthenticationPolicy(callback=groupfinder)


@contextmanager
def authenticated_context(request, socket):
    request.websocket_userid = socket.authenticated_userid

    yield

    request.websocket_userid = None
