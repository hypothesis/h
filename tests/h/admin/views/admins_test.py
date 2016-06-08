# -*- coding: utf-8 -*-

from mock import Mock
from pyramid import httpexceptions
from pyramid.testing import DummyRequest
import pytest

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


@pytest.mark.usefixtures('user_agnos', 'user_bojan')
class TestAdminsAdd(object):

    def test_makes_users_admins(self, user_bojan):
        request = DummyRequest(params={"add": "bojan"})

        views.admins_add(request)

        assert user_bojan.admin

    def test_is_idempotent(self, user_agnos):
        request = DummyRequest(params={"add": "agnos"})

        views.admins_add(request)

        assert user_agnos.admin

    def test_returns_list_of_admin_users(self):
        request = DummyRequest(params={"add": "bojan"})

        result = views.admins_add(request)

        assert set(result['admin_users']) == set(['agnos', 'bojan'])

    def test_returns_list_of_admin_users_even_when_user_not_found(self):
        request = DummyRequest(params={"add": "florp"})

        result = views.admins_add(request)

        assert set(result['admin_users']) == set(['agnos'])

    def test_flashes_when_user_not_found(self):
        request = DummyRequest(params={"add": "florp"})
        request.session.flash = Mock()

        views.admins_add(request)

        assert request.session.flash.call_count == 1

    @pytest.fixture
    def user_agnos(self, db_session):
        from h import models

        agnos = models.User(username='agnos',
                            email='agnos@example.com',
                            password='agn0s',
                            admin=True)
        db_session.add(agnos)
        db_session.flush()

        return agnos

    @pytest.fixture
    def user_bojan(self, db_session):
        from h import models

        bojan = models.User(username='bojan',
                            email='bojan@example.com',
                            password='b0jan')
        db_session.add(bojan)
        db_session.flush()

        return bojan


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
