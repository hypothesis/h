# -*- coding: utf-8 -*-

import datetime

import jwt
from pyramid import exceptions
from pyramid import security
from pyramid import session


def translate_annotation_principals(principals):
    """
    Translate a list of annotation principals to a list of pyramid principals.
    """
    result = set([])
    for principal in principals:
        # Ignore suspicious principals from annotations
        if principal.startswith('system.'):
            continue
        if principal == 'group:__world__':
            result.add(security.Everyone)
        elif principal == 'group:__authenticated__':
            result.add(security.Authenticated)
        else:
            result.add(principal)
    return list(result)


class Client(object):
    def __init__(self, client_id):
        self.client_id = client_id
        self.client_secret = None


def get_client(request, client_id, client_secret=None):
    """Get a :class:`h.oauth.IClient` instance using the configured
    :term:`client factory` and provided ''client_id''.

    Returns the client object created by the factory. Returns ``None`` if the
    factory returns ``None`` or the provided ``client_secret`` parameter
    does not match the ``client_secret`` attribute of the client.
    """
    client = Client(client_id)

    # Allow a default client, hard-coded in the settings.
    if 'h.client_id' in request.registry.settings:
        if client_id == request.registry.settings['h.client_id']:
            if client.client_secret is None:
                client_secret = request.registry.settings['h.client_secret']
                client.client_secret = client_secret

    if client_secret is not None:
        if not jwt.compat.constant_time_compare(client_secret,
                                                client.client_secret):
            return None

    return client


def authenticate_client(request):
    client = None
    user = None

    if request.client_id is None:
        try:
            session.check_csrf_token(request, token='assertion')
        except exceptions.BadCSRFToken:
            return False
        client_id = request.registry.settings['h.client_id']
        client = get_client(request, client_id)
        user = request.authenticated_userid
    elif request.client_secret is not None:
        client_id = request.client_id
        client_secret = request.client_secret
        client = get_client(request, client_id, client_secret)

    request.client = client
    request.user = user
    return request.client is not None


def generate_signed_token(request):
    """Generate a signed JSON Web Token from OAuth attributes of the request.

    A JSON Web Token [jwt]_ is a token that contains a header, describing the
    algorithm used for signing, a set of claims (the payload), and a trailing
    signature.

    .. [jwt] https://tools.ietf.org/html/draft-ietf-oauth-json-web-token
    """
    now = datetime.datetime.utcnow().replace(microsecond=0)
    ttl = datetime.timedelta(seconds=request.expires_in)

    claims = {
        'iss': request.client.client_id,
        'aud': request.host_url,
        'sub': request.user,
        'exp': now + ttl,
        'iat': now,
    }

    return jwt.encode(claims, request.client.client_secret)
