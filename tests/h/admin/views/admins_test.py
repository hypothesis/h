# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock
from pyramid import httpexceptions
from pyramid.testing import DummyRequest
import pytest

from h.admin.views import admins as views


@pytest.mark.usefixtures('routes')
class TestAdminsIndex(object):
    def test_when_no_admins(self):
        request = DummyRequest()

        result = views.admins_index(request)

        assert result["admin_users"] == []

    @pytest.mark.usefixtures('users')
    def test_context_contains_admin_usernames(self):
        request = DummyRequest()

        result = views.admins_index(request)

        assert set(result["admin_users"]) == set(["agnos", "bojan", "cristof"])


@pytest.mark.usefixtures('users', 'routes')
class TestAdminsAddRemove(object):

    def test_add_makes_users_admins(self, users):
        request = DummyRequest(params={"add": "eva"})

        views.admins_add(request)

        assert users['eva'].admin

    def test_add_is_idempotent(self, users):
        request = DummyRequest(params={"add": "agnos"})

        views.admins_add(request)

        assert users['agnos'].admin

    def test_add_redirects_to_index(self):
        request = DummyRequest(params={"add": "eva"})

        result = views.admins_add(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'

    def test_add_redirects_to_index_when_user_not_found(self):
        request = DummyRequest(params={"add": "florp"})

        result = views.admins_add(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'

    def test_add_flashes_when_user_not_found(self):
        request = DummyRequest(params={"add": "florp"})
        request.session.flash = Mock()

        views.admins_add(request)

        assert request.session.flash.call_count == 1

    def test_remove_makes_users_not_admins(self, users):
        request = DummyRequest(params={"remove": "cristof"})

        views.admins_remove(request)

        assert not users['cristof'].admin

    def test_remove_is_idempotent(self, users):
        request = DummyRequest(params={"remove": "eva"})

        views.admins_remove(request)

        assert not users['eva'].admin

    def test_remove_will_not_remove_last_admin(self, users):
        views.admins_remove(DummyRequest(params={"remove": "cristof"}))
        views.admins_remove(DummyRequest(params={"remove": "bojan"}))
        views.admins_remove(DummyRequest(params={"remove": "agnos"}))

        assert users['agnos'].admin

    def test_remove_redirects_to_index(self):
        request = DummyRequest(params={"remove": "agnos"})

        result = views.admins_remove(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'

    def test_remove_redirects_to_index_when_user_not_found(self):
        request = DummyRequest(params={"remove": "florp"})

        result = views.admins_remove(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'


@pytest.fixture
def users(db_session):
    from h import models

    admins = ['agnos', 'bojan', 'cristof']
    nonadmins = ['david', 'eva', 'flora']

    users = {}

    for admin in admins:
        users[admin] = models.User(username=admin,
                                   email=admin + '@example.com',
                                   password='secret',
                                   admin=True)
    for nonadmin in nonadmins:
        users[nonadmin] = models.User(username=nonadmin,
                                      email=nonadmin + '@example.com',
                                      password='secret')

    db_session.add_all(list(users.values()))
    db_session.flush()

    return users


@pytest.fixture
def routes(config):
    config.add_route('admin_admins', '/adm/admins')
