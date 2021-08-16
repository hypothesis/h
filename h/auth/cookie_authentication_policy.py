from h.auth.policy import IdentityBasedPolicy
from h.security import Identity


class CookieAuthenticationPolicy(IdentityBasedPolicy):
    def unauthenticated_userid(self, request):
        """We do not allow the unauthenticated userid to be used."""

    def identity(self, request):
        self._add_vary_by_cookie(request)

        user = request.find_service(name="auth_cookie").verify_cookie()
        if not user:
            return None

        return Identity(user=user)

    def remember(self, request, userid, **kw):
        """Returns a list of headers that are to be set from the source service."""

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

        return request.find_service(name="auth_cookie").create_cookie(userid)

    def forget(self, request):
        """A list of headers which will delete appropriate cookies."""

        self._add_vary_by_cookie(request)

        # Clear the session by invalidating it
        request.session.invalidate()

        return request.find_service(name="auth_cookie").revoke_cookie()

    @staticmethod
    def _add_vary_by_cookie(request):
        def vary_add(request, response):
            vary = set(response.vary if response.vary is not None else [])
            vary.add("Cookie")
            response.vary = list(vary)

        request.add_response_callback(vary_add)
