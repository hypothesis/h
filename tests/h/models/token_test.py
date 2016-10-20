# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import Token


class TestToken(object):
    def test_init_generates_value(self):
        assert Token().value

    def test_get_by_userid_filters_by_userid(self, db_session, factories):
        token_1 = factories.Token(userid='acct:vanessa@example.org')
        token_2 = factories.Token(userid='acct:david@example.org')

        assert Token.get_by_userid(db_session, token_2.userid) == token_2

    def test_get_by_userid_only_returns_the_latest_token(self, db_session, factories):
        token_1 = factories.Token()
        token_2 = factories.Token(userid=token_1.userid)

        assert Token.get_by_userid(db_session, token_1.userid) == token_2
