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


def test_authorized_to_read_returns_True_if_group_world():
    """If 'group:__world__' is in the read permissions it returns True."""
    assert auth.authorized_to_read(
        # No 'group:__world__' or the user's ID in effective_principals.
        effective_principals=['foo', 'bar'],
        annotation={'permissions': {'read': ['group:__world__']}}) is True


def test_authorized_to_read_returns_True_for_user():
    """If user in effective_principals and read permissions it returns True."""
    assert (auth.authorized_to_read(
        effective_principals=['acct:vlad@hypothes.is'],
        annotation={'permissions': {'read': ['acct:vlad@hypothes.is']}})
        is True)


def test_authorized_to_read_returns_True_for_group():
    """If group in effective_principals and read perms it returns True."""
    assert (auth.authorized_to_read(
        effective_principals=['acct:vlad@hypothes.is', 'group:xyzabc'],
        annotation={'permissions': {'read': ['group:xyzabc']}})
        is True)


def test_authorized_to_read_returns_False_for_user_private_annotation():
    """If the annotation is private other users can't read it."""
    assert (auth.authorized_to_read(
        effective_principals=['acct:vlad@hypothes.is', 'group:xyzabc'],
        annotation={'permissions': {'read': ['acct:adam@hypothes.is']}})
        is False)


def test_authorized_to_read_returns_False_for_group_private_annotation():
    """If the user isn't a member of the group they can't read it."""
    assert (auth.authorized_to_read(
        effective_principals=['acct:vlad@hypothes.is', 'group:xyzabc'],
        annotation={'permissions': {'read': ['group:foobar']}})
        is False)


def test_group_principals_with_no_groups():
    user = mock.Mock(groups=[])

    assert auth.group_principals(user, mock.Mock()) == ['group:__none__']


def test_group_principals_with_one_group():
    user = mock.Mock(groups=[_mock_group('hashid1')])

    assert auth.group_principals(user, mock.Mock()) == [
        'group:__none__', 'group:hashid1']


def test_group_principals_with_three_groups():
    user = mock.Mock(groups=[
        _mock_group('hashid1'),
        _mock_group('hashid2'),
        _mock_group('hashid3'),
    ])

    assert auth.group_principals(user, mock.Mock()) == [
        'group:__none__',
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
