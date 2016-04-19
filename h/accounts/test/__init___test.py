# -*- coding: utf-8 -*-
import mock
import pytest
from pyramid import httpexceptions
from pyramid import testing

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


# The fixtures required to mock all of get_user()'s dependencies.
get_user_fixtures = pytest.mark.usefixtures('util', 'get_by_username')


@get_user_fixtures
def test_get_user_calls_split_user(util):
    """It should call split_user() once with the given userid."""
    util.user.split_user.return_value = {
        'username': 'fred', 'domain': 'hypothes.is'}

    accounts.get_user('acct:fred@hypothes.is', mock.Mock())

    util.user.split_user.assert_called_once_with('acct:fred@hypothes.is')


@get_user_fixtures
def test_get_user_returns_None_if_split_user_raises_ValueError(util):
    util.user.split_user.side_effect = ValueError

    assert accounts.get_user('userid', mock.Mock()) is None


@get_user_fixtures
def test_get_user_returns_None_if_domain_does_not_match(util):
    request = mock.Mock(auth_domain='hypothes.is')
    util.user.split_user.return_value = {
        'username': 'username', 'domain': 'other'}

    assert accounts.get_user('userid', request) is None


@get_user_fixtures
def test_get_user_calls_get_by_username(util, get_by_username):
    """It should call get_by_username() once with the username."""
    request = mock.Mock(auth_domain='hypothes.is')
    util.user.split_user.return_value = {
        'username': 'username', 'domain': 'hypothes.is'}

    accounts.get_user('acct:username@hypothes.is', request)

    get_by_username.assert_called_once_with('username')


@get_user_fixtures
def test_get_user_returns_user(util, get_by_username):
    """It should return the result from get_by_username()."""
    request = mock.Mock(auth_domain='hypothes.is')
    util.user.split_user.return_value = {
        'username': 'username', 'domain': 'hypothes.is'}

    assert accounts.get_user('acct:username@hypothes.is', request) == (
        get_by_username.return_value)


authenticated_user_fixtures = pytest.mark.usefixtures('get_user')


@authenticated_user_fixtures
def test_authenticated_user_calls_get_user(authn_policy, get_user):
    """It should call get_user() correctly."""
    request = testing.DummyRequest()
    authn_policy.authenticated_userid.return_value = 'userid'

    accounts.authenticated_user(request)

    get_user.assert_called_once_with('userid', request)


@authenticated_user_fixtures
def test_authenticated_user_invalidates_session_if_user_does_not_exist(
        authn_policy, get_user):
    """It should log the user out if they no longer exist in the db."""
    request = testing.DummyRequest()
    request.current_route_url = lambda: '/'
    request.session.invalidate = mock.Mock()
    authn_policy.authenticated_userid.return_value = 'userid'
    get_user.return_value = None

    try:
        accounts.authenticated_user(request)
    except Exception:
        pass

    request.session.invalidate.assert_called_once_with()


@authenticated_user_fixtures
def test_authenticated_user_does_not_invalidate_session_if_not_authenticated(
        authn_policy, get_user):
    """
    If authenticated_userid is None it shouldn't invalidate the session.

    Even though the user with id None obviously won't exist in the db.

    This also tests that it doesn't raise a redirect in this case.

    """
    request = testing.DummyRequest()
    request.current_route_url = lambda: '/'
    request.session.invalidate = mock.Mock()
    authn_policy.authenticated_userid.return_value = None
    get_user.return_value = None

    accounts.authenticated_user(request)

    assert not request.session.invalidate.called


@authenticated_user_fixtures
def test_authenticated_user_redirects_if_user_does_not_exist(
        authn_policy, get_user):
    request = testing.DummyRequest()
    request.current_route_url = lambda: '/the/page/that/I/was/on'
    authn_policy.authenticated_userid.return_value = 'userid'
    get_user.return_value = None

    with pytest.raises(httpexceptions.HTTPFound) as err:
        accounts.authenticated_user(request)

    assert err.value.location == '/the/page/that/I/was/on', (
        'It should redirect to the same page that was requested')


@authenticated_user_fixtures
def test_authenticated_user_returns_user_from_get_user(get_user):
    """It should return the user from get_user()."""
    request = mock.Mock(authenticated_userid='userid')

    assert accounts.authenticated_user(request) == get_user.return_value


@pytest.fixture
def util(patch):
    return patch('h.accounts.util')


@pytest.fixture
def get_by_username(patch):
    return patch('h.accounts.models.User.get_by_username', autospec=False)


@pytest.fixture
def get_user(patch):
    return patch('h.accounts.get_user')
