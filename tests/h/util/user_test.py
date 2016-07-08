# -*- coding: utf-8 -*-

import pytest

from h.util import user as user_util


def test_split_user():
    parts = user_util.split_user("acct:seanh@hypothes.is")
    assert parts == {'username': 'seanh', 'domain': 'hypothes.is'}


def test_split_user_no_match():
    with pytest.raises(ValueError):
        user_util.split_user("donkeys")


def test_userid_from_username():
    userid = user_util.userid_from_username('douglas', 'example.com')

    assert userid == 'acct:douglas@example.com'
