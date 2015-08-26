# -*- coding: utf-8 -*-
from h import util


def test_split_user():
    parts = util.split_user("acct:seanh@hypothes.is")
    assert parts == ('seanh', 'hypothes.is')


def test_split_user_no_match():
    parts = util.split_user("donkeys")
    assert parts is None
