# -*- coding: utf-8 -*-

import datetime

import jwt

import pytest
from hypothesis import strategies as st
from hypothesis import assume, given

from h.auth import models, tokens

VALID_TOKEN_EXAMPLES = [
    # Valid
    lambda a, k: jwt.encode({'aud': a, 'exp': _seconds_from_now(3600)},
                            key=k),

    # Expired, but within leeway
    lambda a, k: jwt.encode({'aud': a, 'exp': _seconds_from_now(-120)},
                            key=k),
]

INVALID_TOKEN_EXAMPLES = [
    # Expired 1 hour ago
    lambda a, k: jwt.encode({'aud': a, 'exp': _seconds_from_now(-3600)},
                            key=k),

    # Issued in the future
    lambda a, k: jwt.encode({'aud': a,
                             'exp': _seconds_from_now(3600),
                             'iat': _seconds_from_now(1800)},
                            key=k),

    # Incorrect audience
    lambda a, k: jwt.encode({'aud': 'https://bar.com',
                             'exp': _seconds_from_now(3600)},
                            key=k),

    # Incorrect encoding key
    lambda a, k: jwt.encode({'aud': a, 'exp': _seconds_from_now(3600)},
                            key='somethingelse'),
]


class TestLegacyClientJWT(object):
    @pytest.mark.parametrize('get_token', VALID_TOKEN_EXAMPLES)
    def test_ok_for_valid_jwt(self, get_token):
        token = get_token('http://example.com', 'secrets!')

        result = tokens.LegacyClientJWT(token,
                                        audience='http://example.com',
                                        key='secrets!')

        assert isinstance(result, tokens.LegacyClientJWT)

    @pytest.mark.parametrize('get_token', INVALID_TOKEN_EXAMPLES)
    def test_raises_for_invalid_jwt(self, get_token):
        token = get_token('http://example.com', 'secrets!')

        with pytest.raises(jwt.InvalidTokenError):
            tokens.LegacyClientJWT(token,
                                   audience='http://example.com',
                                   key='secrets!')

    def test_payload(self):
        payload = {'aud': 'http://foo.com',
                   'exp': _seconds_from_now(3600),
                   'sub': 'foobar'}
        token = jwt.encode(payload, key='s3cr37')

        result = tokens.LegacyClientJWT(token,
                                        audience='http://foo.com',
                                        key='s3cr37')

        assert result.payload == payload

    def test_userid_gets_payload_sub(self):
        payload = {'aud': 'http://foo.com',
                   'exp': _seconds_from_now(3600),
                   'sub': 'foobar'}
        token = jwt.encode(payload, key='s3cr37')

        result = tokens.LegacyClientJWT(token,
                                        audience='http://foo.com',
                                        key='s3cr37')

        assert result.userid == 'foobar'

    def test_userid_none_if_sub_missing(self):
        payload = {'aud': 'http://foo.com',
                   'exp': _seconds_from_now(3600)}
        token = jwt.encode(payload, key='s3cr37')

        result = tokens.LegacyClientJWT(token,
                                        audience='http://foo.com',
                                        key='s3cr37')

        assert result.userid is None


def test_generate_jwt_calls_encode(jwt_, pyramid_config, pyramid_request):
    """It should pass the right arguments to encode()."""
    pyramid_config.testing_securitypolicy('acct:testuser@hypothes.is')
    before = datetime.datetime.utcnow()

    tokens.generate_jwt(pyramid_request, 3600)

    assert jwt_.encode.call_args[0][0]['sub'] == 'acct:testuser@hypothes.is', (
        "It should encode the userid as 'sub'")
    after = datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)
    assert before < jwt_.encode.call_args[0][0]['exp'] < after, (
        "It should encode the expiration time as 'exp'")
    assert jwt_.encode.call_args[0][0]['aud'] == pyramid_request.host_url, (
        "It should encode request.host_url as 'aud'")
    assert jwt_.encode.call_args[1]['algorithm'] == 'HS256', (
        "It should pass the right algorithm to encode()")


def test_generate_jwt_when_authenticated_userid_is_None(jwt_, pyramid_request):
    """It should work when request.authenticated_userid is None."""
    tokens.generate_jwt(pyramid_request, 3600)

    assert jwt_.encode.call_args[0][0]['sub'] is None


def test_generate_jwt_returns_token(jwt_, pyramid_request):
    result = tokens.generate_jwt(pyramid_request, 3600)

    assert result == jwt_.encode.return_value


@pytest.mark.usefixtures('token')
class TestAuthToken(object):
    def test_retrieves_token_for_request(self, pyramid_request, token):
        pyramid_request.headers['Authorization'] = 'Bearer ' + token.value

        result = tokens.auth_token(pyramid_request)

        assert result == token

    def test_returns_none_when_no_authz_header(self, pyramid_request, token):
        result = tokens.auth_token(pyramid_request)

        assert result is None

    def test_returns_none_for_empty_token(self, pyramid_request, token):
        pyramid_request.headers['Authorization'] = 'Bearer '

        result = tokens.auth_token(pyramid_request)

        assert result is None

    def test_returns_none_for_malformed_header(self, pyramid_request, token):
        pyramid_request.headers['Authorization'] = token.value

        result = tokens.auth_token(pyramid_request)

        assert result is None

    @given(header=st.text())
    @pytest.mark.fuzz
    def test_returns_none_for_malformed_header_fuzz(self,
                                                    header,
                                                    pyramid_request,
                                                    token):
        assume(header != 'Bearer ' + token.value)
        pyramid_request.headers['Authorization'] = header

        result = tokens.auth_token(pyramid_request)

        assert result is None

    def test_returns_none_for_invalid_token(self, pyramid_request):
        pyramid_request.headers['Authorization'] = 'Bearer abcd1234'

        result = tokens.auth_token(pyramid_request)

        assert result is None

    @pytest.mark.usefixture('pyramid_settings')
    def test_returns_legacy_client_jwt_when_jwt(self, pyramid_request):
        token = jwt.encode({'aud': pyramid_request.host_url,
                            'exp': _seconds_from_now(3600)},
                           key='secret')
        pyramid_request.headers['Authorization'] = 'Bearer ' + token

        result = tokens.auth_token(pyramid_request)

        assert isinstance(result, tokens.LegacyClientJWT)

    @pytest.fixture
    def token(self, db_session):
        token = models.Token(userid='acct:foo@example.com')
        db_session.add(token)
        db_session.flush()
        return token


@pytest.fixture
def pyramid_settings(pyramid_settings):
    pyramid_settings.update({
        'h.client_id': 'id',
        'h.client_secret': 'secret',
    })
    return pyramid_settings


@pytest.fixture
def jwt_(patch):
    return patch('h.auth.tokens.jwt')


def _seconds_from_now(seconds):
    return datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
