# -*- coding: utf-8 -*-
from urllib import quote

from annotator import auth
from oauthlib.oauth2 import BackendApplicationServer, RequestValidator
from pyramid.authentication import RemoteUserAuthenticationPolicy

from h.auth.local.models import Consumer


def generate_token(request):
    message = {
        'consumerKey': request.client.key,
        'ttl': request.client.ttl,
    }

    if request.extra_credentials is not None:
        message.update(request.extra_credentials)

    return auth.encode_token(message, request.client.secret)


def get_consumer(request, key):
    inst = Consumer.get_by_key(request, key)

    # Coerce types so elasticsearch doesn't choke on the UUIDs.
    # TODO: Can we add magic to .models.GUID to take care of this?
    result = auth.Consumer(str(key))
    result.secret = str(inst.secret)
    result.ttl = inst.ttl

    return result


class RequestValidator(RequestValidator):
    def __init__(self, request, *args, **kwargs):
        super(RequestValidator, self).__init__(*args, **kwargs)

        # bw compat
        if request.params.get('grant_type') is None:
            persona = request.GET.get('persona')
            if persona is not None:
                request.GET['persona'] = quote(persona)
                request.GET['grant_type'] = 'client_credentials'

        self.request = request
        self.settings = request.registry.settings

    def authenticate_client(self, request):
        key = self.settings['api.key']
        secret = self.settings.get('api.secret')
        ttl = self.settings.get('api.ttl', auth.DEFAULT_TTL)

        if secret is not None:
            consumer = auth.Consumer(key)
            consumer.secret = secret
            consumer.ttl = ttl
        else:
            consumer = get_consumer(self.request, key)

        request.client = consumer
        request.client.client_id = key
        request.client_id = key

        return True

    def get_default_redirect_uri(self, client_id, request):
        return self.request.registry.settings.get('horus.login_redirect', '/')

    def get_default_scopes(self, client, request):
        return ['annotations']

    def save_bearer_token(self, token, request):
        return self.get_default_redirect_uri(request.client_id, request)

    def validate_bearer_token(self, token, scopes, request):
        self.authenticate_client(request)

        try:
            credentials = auth.decode_token(token, request.client.secret)
            request.user = credentials.get('userId')
            return True
        except:
            pass

        return False

    def validate_grant_type(self, client_id, grant_type, client, request):
        if grant_type == 'client_credentials':
            return client_id == client.client_id

        return False

    def validate_scopes(self, client_id, scopes, client, request):
        return scopes == ['annotations']


class LocalAuthenticationPolicy(RemoteUserAuthenticationPolicy):
    def unauthenticated_userid(self, request):
        validator = RequestValidator(request)

        token_generator = generate_token
        server = BackendApplicationServer(validator, token_generator)

        # bw compat
        token = request.environ.get(self.environ_key)
        if token is not None:
            request.authorization = 'Bearer %s' % token

        valid, r = server.verify_request(
            request.url,
            request.method,
            None,
            request.headers,
            ['annotations'],
        )

        if valid:
            return r.user

        # bw compat
        personas = request.session.get('personas', [])
        if len(personas):
            return personas[0]

        return None


def includeme(config):
    registry = config.registry
    settings = registry.settings

    authn_debug = settings.get('pyramid.debug_authorization') \
        or settings.get('debug_authorization')
    authn_policy = LocalAuthenticationPolicy(
        environ_key='HTTP_X_ANNOTATOR_AUTH_TOKEN',
        debug=authn_debug,
    )
    config.set_authentication_policy(authn_policy)
