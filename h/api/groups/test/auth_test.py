# -*- coding: utf-8 -*-
import mock

from h.api.groups import auth


def _mock_group(hashid):
    return mock.Mock(hashid=mock.Mock(return_value=hashid))


def test_group_principals_with_no_groups():
    user = mock.Mock(groups=[])

    assert auth.group_principals(user, mock.Mock()) == ['group:__world__']


def test_group_principals_with_one_group():
    user = mock.Mock(groups=[_mock_group('hashid1')])

    assert auth.group_principals(user, mock.Mock()) == [
        'group:__world__', 'group:hashid1']


def test_group_principals_with_three_groups():
    user = mock.Mock(groups=[
        _mock_group('hashid1'),
        _mock_group('hashid2'),
        _mock_group('hashid3'),
    ])

    assert auth.group_principals(user, mock.Mock()) == [
        'group:__world__', 'group:hashid1', 'group:hashid2', 'group:hashid3']
