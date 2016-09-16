# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from h.models import Token


class TestToken(object):

    def test_token_with_no_expiry_is_valid(self):
        token = Token(userid='acct:foo@example.com')

        assert token.is_valid()

    def test_token_with_future_expiry_is_valid(self):
        token = Token(userid='acct:foo@example.com')
        token.expires = _seconds_from_now(1800)

        assert token.is_valid()

    def test_token_with_past_expiry_is_not_valid(self):
        token = Token(userid='acct:foo@example.com')
        token.expires = _seconds_from_now(-1800)

        assert not token.is_valid()


def _seconds_from_now(seconds):
    return datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
