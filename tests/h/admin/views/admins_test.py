# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from pyramid import httpexceptions
import pytest

from h.admin.views import admins as views


@pytest.mark.usefixtures('routes')
class TestAdminsIndex(object):

    def test_when_no_admins(self, pyramid_request):
        result = views.admins_index(pyramid_request)

        assert result["admin_users"] == []

    @pytest.mark.usefixtures('users')
    def test_context_contains_admin_usernames(self, pyramid_request):
        result = views.admins_index(pyramid_request)

        assert set(result["admin_users"]) == set(["agnos", "bojan", "cristof"])


@pytest.mark.usefixtures('users', 'routes')
class TestAdminsAddRemove(object):

    def test_add_makes_users_admins(self, pyramid_request, users):
        pyramid_request.params = {"add": "eva"}

        views.admins_add(pyramid_request)

        assert users['eva'].admin

    def test_add_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {"add": "agnos"}

        views.admins_add(pyramid_request)

        assert users['agnos'].admin

    def test_add_strips_spaces(self, pyramid_request, users):
        pyramid_request.params = {"add": "   david   "}

        views.admins_add(pyramid_request)

        assert users['david'].admin

    def test_add_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"add": "eva"}

        result = views.admins_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'

    def test_add_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"add": "florp"}

        result = views.admins_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'

    def test_add_flashes_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"add": "florp"}
        pyramid_request.session.flash = mock.Mock()

        views.admins_add(pyramid_request)

        assert pyramid_request.session.flash.call_count == 1

    def test_remove_makes_users_not_admins(self, pyramid_request, users):
        pyramid_request.params = {"remove": "cristof"}

        views.admins_remove(pyramid_request)

        assert not users['cristof'].admin

    def test_remove_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {"remove": "eva"}

        views.admins_remove(pyramid_request)

        assert not users['eva'].admin

    def test_remove_will_not_remove_last_admin(self, pyramid_request, users):
        pyramid_request.params = {"remove": "cristof"}
        views.admins_remove(pyramid_request)
        pyramid_request.params = {"remove": "bojan"}
        views.admins_remove(pyramid_request)
        pyramid_request.params = {"remove": "agnos"}
        views.admins_remove(pyramid_request)

        assert users['agnos'].admin

    def test_remove_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"remove": "agnos"}

        result = views.admins_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'

    def test_remove_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"remove": "florp"}

        result = views.admins_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/admins'


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('admin_admins', '/adm/admins')


@pytest.fixture
def users(db_session, factories):
    admins = ['agnos', 'bojan', 'cristof']
    nonadmins = ['david', 'eva', 'flora']

    users = {}

    for admin in admins:
        users[admin] = factories.User(username=admin, admin=True)
    for nonadmin in nonadmins:
        users[nonadmin] = factories.User(username=nonadmin)

    db_session.add_all(list(users.values()))
    db_session.flush()

    return users
