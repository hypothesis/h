# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from pyramid import httpexceptions
import pytest

from h.admin.views import staff as views


@pytest.mark.usefixtures('routes')
class TestStaffIndex(object):
    def test_when_no_staff(self, pyramid_request):
        result = views.staff_index(pyramid_request)

        assert result["staff"] == []

    @pytest.mark.usefixtures('users')
    def test_context_contains_staff_usernames(self, pyramid_request):
        result = views.staff_index(pyramid_request)

        assert set(result["staff"]) == set(["agnos", "bojan", "cristof"])


@pytest.mark.usefixtures('users', 'routes')
class TestStaffAddRemove(object):

    def test_add_makes_users_staff(self, pyramid_request, users):
        pyramid_request.params = {"add": "eva"}

        views.staff_add(pyramid_request)

        assert users['eva'].staff

    def test_add_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {"add": "agnos"}

        views.staff_add(pyramid_request)

        assert users['agnos'].staff

    def test_add_strips_spaces(self, pyramid_request, users):
        pyramid_request.params = {"add": "   eva   "}

        views.staff_add(pyramid_request)

        assert users['eva'].staff

    def test_add_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"add": "eva"}

        result = views.staff_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_add_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"add": "florp"}

        result = views.staff_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_add_flashes_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"add": "florp"}
        pyramid_request.session.flash = mock.Mock()

        views.staff_add(pyramid_request)

        assert pyramid_request.session.flash.call_count == 1

    def test_remove_makes_users_not_staff(self, pyramid_request, users):
        pyramid_request.params = {"remove": "cristof"}

        views.staff_remove(pyramid_request)

        assert not users['cristof'].staff

    def test_remove_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {"remove": "eva"}

        views.staff_remove(pyramid_request)

        assert not users['eva'].staff

    def test_remove_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"remove": "agnos"}

        result = views.staff_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_remove_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"remove": "florp"}

        result = views.staff_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('admin_staff', '/adm/staff')


@pytest.fixture
def users(db_session, factories):
    staff = ['agnos', 'bojan', 'cristof']
    nonstaff = ['david', 'eva', 'flora']

    users = {}

    for staff in staff:
        users[staff] = factories.User(username=staff, staff=True)
    for nonstaff in nonstaff:
        users[nonstaff] = factories.User(username=nonstaff)

    db_session.add_all(list(users.values()))
    db_session.flush()

    return users
