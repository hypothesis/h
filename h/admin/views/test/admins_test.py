# -*- coding: utf-8 -*-

from mock import Mock
from pyramid import httpexceptions
from pyramid.testing import DummyRequest
import pytest

from h import accounts
from h.admin.views import admins as views


# The fixtures required to mock all of admins_index()'s dependencies.
admins_index_fixtures = pytest.mark.usefixtures('User')


@admins_index_fixtures
def test_admins_index_when_no_admins(User):
    request = DummyRequest()
    User.admins.return_value = []

    result = views.admins_index(request)

    assert result["admin_users"] == []


@admins_index_fixtures
def test_admins_index_when_one_admin(User):
    request = DummyRequest()
    User.admins.return_value = [Mock(username="fred")]

    result = views.admins_index(request)

    assert result["admin_users"] == ["fred"]


@admins_index_fixtures
def test_admins_index_when_multiple_admins(User):
    request = DummyRequest()
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]

    result = views.admins_index(request)

    assert result["admin_users"] == ["fred", "bob", "frank"]


# The fixtures required to mock all of admins_add()'s dependencies.
admins_add_fixtures = pytest.mark.usefixtures('make_admin', 'admins_index')


@admins_add_fixtures
def test_admins_add_calls_make_admin(make_admin):
    request = DummyRequest(params={"add": "seanh"})

    views.admins_add(request)

    make_admin.assert_called_once_with("seanh")


@admins_add_fixtures
def test_admins_add_returns_index_on_success(admins_index):
    request = DummyRequest(params={"add": "seanh"})
    admins_index.return_value = "expected data"

    result = views.admins_add(request)

    assert result == "expected data"


@admins_add_fixtures
def test_admins_add_flashes_on_NoSuchUserError(make_admin):
    make_admin.side_effect = accounts.NoSuchUserError
    request = DummyRequest(params={"add": "seanh"})
    request.session.flash = Mock()

    views.admins_add(request)

    assert request.session.flash.call_count == 1


@admins_add_fixtures
def test_admins_add_returns_index_on_NoSuchUserError(make_admin, admins_index):
    make_admin.side_effect = accounts.NoSuchUserError
    admins_index.return_value = "expected data"
    request = DummyRequest(params={"add": "seanh"})

    result = views.admins_add(request)

    assert result == "expected data"


# The fixtures required to mock all of admins_remove()'s dependencies.
admins_remove_fixtures = pytest.mark.usefixtures('User')


@admins_remove_fixtures
def test_admins_remove_calls_get_by_username(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})

    views.admins_remove(request)

    User.get_by_username.assert_called_once_with("fred")


@admins_remove_fixtures
def test_admins_remove_sets_admin_to_False(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    user = Mock(admin=True)
    User.get_by_username.return_value = user

    views.admins_remove(request)

    assert user.admin is False


@admins_remove_fixtures
def test_admins_remove_returns_redirect_on_success(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})

    response = views.admins_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


@admins_remove_fixtures
def test_admins_remove_returns_redirect_when_too_few_admins(User):
    User.admins.return_value = [Mock(username="fred")]
    request = DummyRequest(params={"remove": "fred"})

    response = views.admins_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


@admins_remove_fixtures
def test_admins_remove_does_not_delete_last_admin(User):
    User.admins.return_value = [Mock(username="fred")]
    request = DummyRequest(params={"remove": "fred"})
    user = Mock(admin=True)
    User.get_by_username.return_value = user

    views.admins_remove(request)

    assert user.admin is True


@pytest.fixture(autouse=True)
def routes(config):
    config.add_route('admin_admins', '/adm/admins')


@pytest.fixture
def User(patch):
    return patch('h.models.User')


@pytest.fixture
def admins_index(patch):
    return patch('h.admin.views.admins.admins_index')


@pytest.fixture
def make_admin(patch):
    return patch('h.admin.views.admins.accounts.make_admin')
