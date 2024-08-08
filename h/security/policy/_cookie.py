from pyramid.security import Allowed, Denied
from webob.cookies import SignedCookieProfile

from h.security.identity import Identity
from h.security.permits import identity_permits
from h.security.policy.helpers import AuthTicketCookieHelper


class CookiePolicy:
    """
    An authentication policy based on cookies.

    This policy kicks in when accessing the UI presented by `h` and also boot
    straps the login for the client (when the popup shows).
    """

    def __init__(
        self,
        html_authcookie: SignedCookieProfile,
        api_authcookie: SignedCookieProfile,
        helper: AuthTicketCookieHelper,
    ):
        self.html_authcookie = html_authcookie
        self.api_authcookie = api_authcookie
        self.helper = helper

    def identity(self, request):
        self.helper.add_vary_by_cookie(request)
        return self.helper.identity(self.html_authcookie, request)

    def authenticated_userid(self, request):
        return Identity.authenticated_userid(self.identity(request))

    def remember(self, request, userid, **kw):  # pylint:disable=unused-argument
        self.helper.add_vary_by_cookie(request)

        previous_userid = self.authenticated_userid(request)

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

        return [
            *self.helper.remember(self.html_authcookie, request, userid),
            *self.helper.remember(self.api_authcookie, request, userid),
        ]

    def forget(self, request):
        self.helper.add_vary_by_cookie(request)
        return [
            *self.helper.forget(self.html_authcookie, request),
            *self.helper.forget(self.api_authcookie, request),
        ]

    def permits(self, request, context, permission) -> Allowed | Denied:
        return identity_permits(self.identity(request), context, permission)
