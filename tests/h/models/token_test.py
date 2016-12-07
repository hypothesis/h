# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import Token


class TestToken(object):
    def test_init_generates_value(self):
        assert Token().value

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
