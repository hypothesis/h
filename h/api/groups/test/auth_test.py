import mock

from h.api.groups import auth


def _mock_group(hashid):
    return mock.Mock(hashid=mock.Mock(return_value=hashid))


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

    assert auth.group_principals(
        user, 'acct:nils@hypothes.is', mock.Mock()) == ['group:__none__']


def test_group_principals_with_one_group():
    user = mock.Mock(groups=[_mock_group('hashid1')])

    assert auth.group_principals(
        user, 'acct:nils@hypothes.is', mock.Mock()) == [
            'group:__none__', 'group:hashid1',
            'acct:nils@hypothes.is~group:hashid1']


def test_group_principals_with_three_groups():
    user = mock.Mock(groups=[
        _mock_group('hashid1'),
        _mock_group('hashid2'),
        _mock_group('hashid3'),
    ])

    assert auth.group_principals(
        user, 'acct:nils@hypothes.is', mock.Mock()) == [
            'group:__none__', 'group:hashid1', 'group:hashid2',
            'group:hashid3', 'acct:nils@hypothes.is~group:hashid1',
            'acct:nils@hypothes.is~group:hashid2',
            'acct:nils@hypothes.is~group:hashid3']
