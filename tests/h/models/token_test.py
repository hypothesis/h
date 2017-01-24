# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from h.models import Token


class TestToken(object):
    def test_init_dev_token(self):
        userid = 'acct:test@hypothes.is'

        dev_token = Token(userid=userid)

        assert dev_token.userid == userid
        assert dev_token.value
        assert dev_token.value.startswith("6879-")
        assert not dev_token.expires
        assert not dev_token.authclient

    def test_init_access_token(self):
        userid = 'acct:test@hypothes.is'
        expires = one_hour_from_now()
        authclient = 'example.com'

        access_token = Token(userid=userid,
                             expires=expires,
                             authclient=authclient)

        assert access_token.userid == userid
        assert access_token.value
        assert access_token.value.startswith("6879-")
        assert access_token.expires == expires
        assert access_token.authclient == authclient

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


def one_hour_from_now():
    return datetime.datetime.now() + datetime.timedelta(hours=1)
