# -*- coding: utf-8 -*-
from annotator import auth
from oauthlib import oauth2

from ..auth import utils


def expires_in(request):
    return request.client.ttl


def token_generator(request):
    client = utils.get_consumer(request)
    consumer = request.consumer
    credentials = request.extra_credentials or {}
    credentials['consumerKey'] = consumer.client_id
    credentials['ttl'] = consumer.ttl
    if request.user is not None:
        credentials['userId'] = request.user
    return auth.encode_token(credentials, client.client_secret)


class AnnotatorToken(oauth2.BearerToken):
    def __init__(self, request_validator=None):
        super(AnnotatorToken, self).__init__(
            request_validator=request_validator,
            token_generator=token_generator,
            expires_in=expires_in
        )

    def validate_request(self, request):
        token = request.headers.get('X-Annotator-Auth-Token')
        return self.request_validator.validate_bearer_token(
            token, request.scopes, request)

    def estimate_type(self, request):
        if 'X-Annotator-Auth-Token' in request.headers:
            return 0
        else:
            return 9
