import logging

from pyramid.security import Allowed, Denied
from webob.cookies import SignedCookieProfile

from h.security.identity import Identity
from h.security.permits import identity_permits
from h.security.policy.helpers import AuthTicketCookieHelper

log = logging.getLogger(__name__)


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
        identity, auth_ticket = self.helper.identity(self.html_authcookie, request)

        # If a request was successfully authenticated using the HTML auth
        # cookie and that request did *not* also contain the API auth cookie,
        # then add the API auth cookie to the user's browser.
        #
        # This was necessary when first adding the API auth cookie:
        # we needed to add the API auth cookie to the browsers of users who
        # were already logged in with just the HTML auth cookie, we couldn't
        # just rely on logging in to set the API auth cookie for users who were
        # *already* logged in.
        #
        # This also gets around other situations where a browser somehow has
        # our HTML auth cookie but does not have our API auth cookie. Normally
        # this won't happen but it could happen if the API auth cookie (but not
        # the HTML one) was deleted somehow, for example by the user manually
        # deleting the cookie in the browser's developer tools, or another way.
        self._issue_api_authcookie(identity, request, auth_ticket)

        return identity

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

        # We're about to add the response headers to set the API auth cookie.
        # Set this attribute so that _issue_api_authcookie() below won't add
        # the same headers again. Otherwise responses to login form submissions
        # would set the same cookie twice.
        request.h_api_authcookie_headers_added = True

        auth_ticket = self.helper.add_ticket(request, userid)

        return [
            *self.helper.remember(self.html_authcookie, userid, auth_ticket),
            *self.helper.remember(self.api_authcookie, userid, auth_ticket),
        ]

    def forget(self, request):
        self.helper.add_vary_by_cookie(request)
        return [
            *self.helper.forget(self.html_authcookie, request),
            *self.helper.forget(self.api_authcookie, request),
        ]

    def permits(self, request, context, permission) -> Allowed | Denied:
        return identity_permits(self.identity(request), context, permission)

    def _issue_api_authcookie(self, identity, request, auth_ticket):
        if not identity:
            return

        if not identity.user:
            return

        if self.api_authcookie.cookie_name in request.cookies:
            return

        if hasattr(request, "h_api_authcookie_headers_added"):
            return

        headers = self.helper.remember(
            self.api_authcookie, identity.user.userid, auth_ticket
        )

        def add_api_authcookie_headers(
            request,  # pylint:disable=unused-argument
            response,
        ):
            log.info("Fixing missing API auth cookie")
            for key, value in headers:
                response.headerlist.append((key, value))

        request.add_response_callback(add_api_authcookie_headers)
        request.h_api_authcookie_headers_added = True
