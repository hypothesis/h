import base64
import os

from pyramid.interfaces import IAuthenticationPolicy, ISessionFactory
from zope.interface import implementer

from h.auth.policy import IdentityBasedPolicy
from h.security import Identity

UNSET = object()


@implementer(IAuthenticationPolicy)
class AuthServicePolicy(IdentityBasedPolicy):
    _have_session = UNSET

    def unauthenticated_userid(self, request):
        """We do not allow the unauthenticated userid to be used."""

    def identity(self, request):
        auth_svc = request.find_service(name="auth_ticket")
        self._add_vary_by_cookie(request)

        # Another method has already verified the user for us!
        if auth_svc.user:
            return Identity(user=auth_svc.user)

        userid, ticket = request.auth_cookie.get_value()

        if user := auth_svc.verify_ticket(userid, ticket):
            return Identity(user=user)

        return None

    def remember(self, request, userid, **kw):
        """Returns a list of headers that are to be set from the source service."""
        if self._have_session is UNSET:
            self._have_session = self._session_registered(request)

        prev_userid = self.authenticated_userid(request)
        self._add_vary_by_cookie(request)

        ticket = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")

        request.find_service(name="auth_ticket").add_ticket(userid, ticket)

        # Clear the previous session
        if self._have_session:
            if prev_userid != userid:
                request.session.invalidate()
            else:
                # We are logging in the same user that is already logged in, we
                # still want to generate a new session, but we can keep the
                # existing data
                data = dict(request.session.items())
                request.session.invalidate()
                request.session.update(data)
                request.session.new_csrf_token()

        return request.auth_cookie.headers_remember([userid, ticket])

    def forget(self, request):
        """A list of headers which will delete appropriate cookies."""

        if self._have_session is UNSET:
            self._have_session = self._session_registered(request)

        self._add_vary_by_cookie(request)

        _, ticket = request.auth_cookie.get_value()
        request.find_service(name="auth_ticket").remove_ticket(ticket)

        # Clear the session by invalidating it
        if self._have_session:
            request.session.invalidate()

        return request.auth_cookie.headers_forget()

    @staticmethod
    def _add_vary_by_cookie(request):
        def vary_add(request, response):
            vary = set(response.vary if response.vary is not None else [])
            vary.add("Cookie")
            response.vary = list(vary)

        request.add_response_callback(vary_add)

    @staticmethod
    def _session_registered(request):
        factory = request.registry.queryUtility(ISessionFactory)

        return False if factory is None else True
