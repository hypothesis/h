# -*- coding: utf-8 -*-
import pytest
import mock

from h import util


def test_split_user():
    parts = util.split_user("acct:seanh@hypothes.is")
    assert parts == {'username': 'seanh', 'domain': 'hypothes.is'}


def test_split_user_no_match():
    with pytest.raises(ValueError):
        parts = util.split_user("donkeys")


def test_userid_from_username_uses_request_dot_auth_domain():
    """It should use the h.auth_domain setting if set."""
    userid = util.userid_from_username(
        'douglas',
        mock.Mock(auth_domain='example.com')
    )

    assert userid == 'acct:douglas@example.com'
