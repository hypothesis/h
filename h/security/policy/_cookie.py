from functools import lru_cache

from h.security.identity import Identity
from h.security.policy._identity_base import IdentityBasedPolicy
from h.services.auth_cookie import AuthCookieService


class CookiePolicy(IdentityBasedPolicy):
    """
    An authentication policy based on cookies.

    This policy kicks in when accessing the UI presented by `h` and also boot
    straps the login for the client (when the popup shows).
    """

    def identity(self, request):
        self._add_vary_by_cookie(request)

        user = request.find_service(AuthCookieService).verify_cookie()
        if not user:
            return None

        return Identity.from_models(user=user)

    def remember(self, request, userid, **kw):  # pylint:disable=unused-argument
        """Get a list of headers which will remember the user in a cookie."""

        self._add_vary_by_cookie(request)

        previous_userid = self.authenticated_userid(request)

        # Clear the previous session
        if previous_userid != userid:
            request.session.invalidate()
        else:
            # We are logging in the same user that is already logged in, we
            # still want to generate a new session, but we can keep the
            # existing data
            data = dict(request.session.items())
            request.session.invalidate()
            request.session.update(data)
            request.session.new_csrf_token()

        return request.find_service(AuthCookieService).create_cookie(userid)

    def forget(self, request):
        """Get a list of headers which will delete appropriate cookies."""

        self._add_vary_by_cookie(request)

        # Clear the session by invalidating it
        request.session.invalidate()

        return request.find_service(AuthCookieService).revoke_cookie()

    @staticmethod
    @lru_cache  # Ensure we only add this once per request
    def _add_vary_by_cookie(request):
        def vary_add(request, response):  # pylint:disable=unused-argument
            vary = set(response.vary if response.vary is not None else [])
            vary.add("Cookie")
            response.vary = list(vary)

        request.add_response_callback(vary_add)
