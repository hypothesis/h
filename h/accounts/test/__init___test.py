# -*- coding: utf-8 -*-
import mock
import pytest

from h import accounts


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_admin_gets_user_by_username(get_by_username):
    """It should pass the right value to get_by_username()."""
    accounts.make_admin("fred")

    get_by_username.assert_called_once_with("fred")


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_admin_sets_admin_to_True_if_False(get_by_username):
    """It should set .admin to True if it was False."""
    fred = mock.Mock()
    fred.admin = False
    get_by_username.return_value = fred

    accounts.make_admin("fred")

    assert fred.admin is True


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_admin_sets_admin_to_True_if_True(get_by_username):
    """If .admin is True it should just do nothing."""
    fred = mock.Mock()
    fred.admin = True
    get_by_username.return_value = fred

    accounts.make_admin("fred")

    assert fred.admin is True


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_admin_raises_if_user_does_not_exist(get_by_username):
    """It should raise NoSuchUserError if the user doesn't exist."""
    get_by_username.return_value = None

    with pytest.raises(accounts.NoSuchUserError):
        accounts.make_admin("fred")


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_staff_gets_user_by_username(get_by_username):
    """It should pass the right value to get_by_username()."""
    accounts.make_staff("fred")

    get_by_username.assert_called_once_with("fred")


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_staff_sets_staff_to_True_if_False(get_by_username):
    """It should set .staff to True if it was False."""
    fred = mock.Mock()
    fred.staff = False
    get_by_username.return_value = fred

    accounts.make_staff("fred")

    assert fred.staff is True


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_staff_sets_staff_to_True_if_True(get_by_username):
    """If .staff is True it should just do nothing."""
    fred = mock.Mock()
    fred.staff = True
    get_by_username.return_value = fred

    accounts.make_staff("fred")

    assert fred.staff is True


@mock.patch("h.accounts.models.User.get_by_username")
def test_make_staff_raises_if_user_does_not_exist(get_by_username):
    """It should raise NoSuchUserError if the user doesn't exist."""
    get_by_username.return_value = None

    with pytest.raises(accounts.NoSuchUserError):
        accounts.make_staff("fred")


# The fixtures required to mock all of user()'s dependencies.
user_fixtures = pytest.mark.usefixtures('util', 'get_by_username')


@user_fixtures
def test_authenticated_user_calls_split_user(util):
    """It should call split_user() once with the given userid."""
    util.split_user.return_value = {
        'username': 'fred', 'domain': 'hypothes.is'}

    accounts.authenticated_user(
        mock.Mock(authenticated_userid='acct:fred@hypothes.is'))

    util.split_user.assert_called_once_with('acct:fred@hypothes.is')


@user_fixtures
def test_authenticated_user_calls_get_by_username(util, get_by_username):
    """It should call get_by_username() once with the username."""
    util.split_user.return_value = {
        'username': 'username', 'domain': 'domain'}

    accounts.authenticated_user(
        mock.Mock(authenticated_userid='acct:username@domain'))

    get_by_username.assert_called_once_with('username')


@user_fixtures
def test_authenticated_user_returns_user(util, get_by_username):
    """It should return the result from get_by_username()."""
    util.split_user.return_value = {
        'username': 'username', 'domain': 'domain'}

    user = accounts.authenticated_user(
        mock.Mock(authenticated_userid='acct:username@domain'))

    assert user == get_by_username.return_value


@pytest.fixture
def util(request):
    patcher = mock.patch('h.accounts.util')
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def get_by_username(request):
    patcher = mock.patch('h.accounts.models.User.get_by_username')
    request.addfinalizer(patcher.stop)
    return patcher.start()
