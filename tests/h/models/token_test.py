# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import pytest

from h.models import Token


@pytest.mark.usefixtures('security')
class TestToken(object):
    def test_init_dev_token(self, security):
        userid = 'acct:test@hypothes.is'

        dev_token = Token(userid=userid)

        assert dev_token.userid == userid
        assert dev_token.value.startswith(Token.prefix)
        assert dev_token.value[len(Token.prefix):] in security.token_urlsafe.side_effect.generated_tokens
        assert not dev_token.expires
        assert not dev_token.authclient
        assert not dev_token.refresh_token

    def test_init_access_token(self, security):
        userid = 'acct:test@hypothes.is'
        expires = one_hour_from_now()
        authclient = 'example.com'

        access_token = Token(userid=userid,
                             expires=expires,
                             authclient=authclient)

        assert access_token.userid == userid
        assert access_token.value.startswith(Token.prefix)
        assert access_token.value[len(Token.prefix):] in security.token_urlsafe.side_effect.generated_tokens
        assert access_token.expires == expires
        assert access_token.authclient == authclient
        assert access_token.refresh_token in security.token_urlsafe.side_effect.generated_tokens

    def test_get_by_refresh_token_returns_the_token(self, db_session, factories):
        refresh_token = 'xyz123'
        # A token that should *not* be returned.
        factories.Token(refresh_token='something_else')
        # The token that should be returned.
        expected_token = factories.Token(refresh_token=refresh_token)
        # Another token that should not be returned.
        factories.Token()

        returned_token = Token.get_by_refresh_token(db_session, refresh_token)

        assert returned_token == expected_token

    def test_get_by_refresh_token_returns_None_if_theres_no_token(self, db_session, factories):
        refresh_token = 'xyz123'
        # A token that should *not* be returned.
        factories.Token(refresh_token='something_else')
        # Another token that should not be returned.
        factories.Token()

        assert Token.get_by_refresh_token(db_session, refresh_token) is None

    def test_get_dev_token_by_userid_filters_by_userid(self, db_session, factories):
        token_1 = factories.Token(userid='acct:vanessa@example.org', authclient=None)
        token_2 = factories.Token(userid='acct:david@example.org', authclient=None)

        assert Token.get_dev_token_by_userid(db_session, token_2.userid) == token_2

    def test_get_dev_token_by_userid_only_returns_the_latest_token(self, db_session, factories):
        token_1 = factories.Token(authclient=None)
        token_2 = factories.Token(userid=token_1.userid, authclient=None)

        assert Token.get_dev_token_by_userid(db_session, token_1.userid) == token_2

    def test_get_dev_token_by_userid_filters_out_non_dev_tokens(self, db_session, factories):
        token = factories.Token(authclient=factories.AuthClient())

        assert Token.get_dev_token_by_userid(db_session, token.userid) is None

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
