import mock

from h.api.groups import auth


def _mock_group(hashid):
    return mock.Mock(hashid=mock.Mock(return_value=hashid))


def test_authorized_to_write_to_group_returns_False_if_no_principal():
    authorized = auth.authorized_to_write_group(
        effective_principals=['foo', 'bar', 'group:other'],
        group_hashid='test-group')

    assert authorized is False


def test_authorized_to_write_to_group_returns_True_if_principal():
    authorized = auth.authorized_to_write_group(
        effective_principals=['foo', 'bar', 'group:other', 'group:test-group'],
        group_hashid='test-group')

    assert authorized is True


def test_authorized_to_write_to_group_returns_True_if_no_group():
    authorized = auth.authorized_to_write_group(
        effective_principals=['foo', 'bar', 'group:other'], group_hashid=None)

    assert authorized is True


def test_authorized_to_read_group_returns_True_if_no_group():
    assert auth.authorized_to_read_group([], None) is True


def test_authorized_to_read_group_returns_True_if_principal():
    authorized = auth.authorized_to_read_group(
        ['foo', 'bar', 'group:other', 'group:test-group'], 'test-group')

    assert authorized is True


def test_authorized_to_read_group_returns_False_if_no_principal():
    authorized = auth.authorized_to_read_group(
        ['foo', 'bar', 'group:other'], 'test-group')

    assert authorized is False


def test_group_principals_with_no_groups():
    user = mock.Mock(groups=[])

    assert auth.group_principals(user, mock.Mock()) == []


def test_group_principals_with_one_group():
    user = mock.Mock(groups=[_mock_group('hashid1')])

    assert auth.group_principals(user, mock.Mock()) == ['group:hashid1']


def test_group_principals_with_three_groups():
    user = mock.Mock(groups=[
        _mock_group('hashid1'),
        _mock_group('hashid2'),
        _mock_group('hashid3'),
    ])

    assert auth.group_principals(user, mock.Mock()) == [
        'group:hashid1',
        'group:hashid2',
        'group:hashid3'
    ]


def test_group_principals_calls_hashid():
    group1 = _mock_group('hashid1')
    group2 = _mock_group('hashid2')
    group3 = _mock_group('hashid3')
    user = mock.Mock(groups=[group1, group2, group3])
    request = mock.Mock()

    auth.group_principals(user, request)

    group1.hashid.assert_called_once_with(request)
    group2.hashid.assert_called_once_with(request)
    group3.hashid.assert_called_once_with(request)
