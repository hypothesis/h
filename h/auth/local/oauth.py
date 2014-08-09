import uuid

from oauthlib.oauth2 import ClientCredentialsGrant, InvalidClientError
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.exceptions import BadCSRFToken
from pyramid.session import check_csrf_token, SignedCookieSessionFactory

from h.api import get_consumer


class SessionGrant(ClientCredentialsGrant):
    def validate_token_request(self, request):
        # bw compat
        persona = request.params.get('persona')
        if persona is not None:
            if persona not in request.session.get('personas', []):
                raise InvalidClientError(request=request)
        else:
            try:
                check_csrf_token(request, token='assertion')
            except BadCSRFToken:
                raise InvalidClientError(request=request)

        request.client = get_consumer(request)

        if request.client is None:
            raise InvalidClientError(request=request)

        request.client_id = request.client_id or request.client.client_id


def includeme(config):
    config.include('pyramid_oauthlib')
    config.add_grant_type(SessionGrant)

    # Configure the authentication policy
    authn_debug = config.registry.settings.get('debug_authorization')
    authn_policy = SessionAuthenticationPolicy(prefix='', debug=authn_debug)
    config.set_authentication_policy(authn_policy)

    # Configure the session
    random_secret = uuid.uuid4().hex + uuid.uuid4().hex
    session_factory = SignedCookieSessionFactory(random_secret)
    config.set_session_factory(session_factory)
