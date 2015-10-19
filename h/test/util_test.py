# -*- coding: utf-8 -*-
import mock

from h import util


def test_split_user():
    parts = util.split_user("acct:seanh@hypothes.is")
    assert parts == ('seanh', 'hypothes.is')


def test_split_user_no_match():
    parts = util.split_user("donkeys")
    assert parts is None


def test_userid_from_username_uses_auth_domain_setting():
    """It should use the h.auth_domain setting if set."""
    userid = util.userid_from_username(
        'douglas',
        mock.Mock(
            domain='should_not_be_used.com',
            registry=mock.Mock(
                settings={'h.auth_domain': 'example.com'})))

    assert userid == 'acct:douglas@example.com'


def test_userid_from_username_falls_back_on_request_domain():
    """It should use request.domain if there's no h.auth_domain setting."""
    userid = util.userid_from_username(
        'douglas',
        mock.Mock(domain='example.com', registry=mock.Mock(settings={})))

    assert userid == 'acct:douglas@example.com'
