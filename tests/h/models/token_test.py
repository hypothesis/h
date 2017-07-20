# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import pytest

from h.models import Token


@pytest.mark.usefixtures('security')
class TestToken(object):
    def test_ttl_is_none_if_token_has_no_expires(self):
        assert Token().ttl is None

    def test_ttl_when_token_does_expire(self):
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        token = Token(expires=expires)

        assert 0 < token.ttl < 3601

    def test_expired_is_false_if_expires_is_in_the_future(self):
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        token = Token(expires=expires)

        assert token.expired is False

    def test_expired_is_false_if_expires_is_none(self):
        token = Token(expires=None)

        assert token.expired is False

    def test_expired_is_true_if_expires_is_in_the_past(self):
        expires = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        token = Token(expires=expires)

        assert token.expired is True

    @pytest.fixture
    def security(self, patch):
        security = patch('h.models.token.security')

        class TestTokenGenerator(object):
            """Return "TOKEN_1", then "TOKEN_2" and so on."""

            def __init__(self):
                self.i = 1
                self.generated_tokens = []

            def __call__(self):
                self.generated_tokens.append("TOKEN_" + str(self.i))
                self.i += 1
                return self.generated_tokens[-1]

        security.token_urlsafe.side_effect = TestTokenGenerator()
        return security


def one_hour_from_now():
    return datetime.datetime.now() + datetime.timedelta(hours=1)
