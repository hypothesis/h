# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock
from pyramid import httpexceptions
from pyramid.testing import DummyRequest
import pytest

from h.admin.views import staff as views


@pytest.mark.usefixtures('routes')
class TestStaffIndex(object):
    def test_when_no_staff(self):
        request = DummyRequest()

        result = views.staff_index(request)

        assert result["staff"] == []

    @pytest.mark.usefixtures('users')
    def test_context_contains_staff_usernames(self):
        request = DummyRequest()

        result = views.staff_index(request)

        assert set(result["staff"]) == set(["agnos", "bojan", "cristof"])


@pytest.mark.usefixtures('users', 'routes')
class TestStaffAddRemove(object):

    def test_add_makes_users_staff(self, users):
        request = DummyRequest(params={"add": "eva"})

        views.staff_add(request)

        assert users['eva'].staff

    def test_add_is_idempotent(self, users):
        request = DummyRequest(params={"add": "agnos"})

        views.staff_add(request)

        assert users['agnos'].staff

    def test_add_redirects_to_index(self):
        request = DummyRequest(params={"add": "eva"})

        result = views.staff_add(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_add_redirects_to_index_when_user_not_found(self):
        request = DummyRequest(params={"add": "florp"})

        result = views.staff_add(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_add_flashes_when_user_not_found(self):
        request = DummyRequest(params={"add": "florp"})
        request.session.flash = Mock()

        views.staff_add(request)

        assert request.session.flash.call_count == 1

    def test_remove_makes_users_not_staff(self, users):
        request = DummyRequest(params={"remove": "cristof"})

        views.staff_remove(request)

        assert not users['cristof'].staff

    def test_remove_is_idempotent(self, users):
        request = DummyRequest(params={"remove": "eva"})

        views.staff_remove(request)

        assert not users['eva'].staff

    def test_remove_redirects_to_index(self):
        request = DummyRequest(params={"remove": "agnos"})

        result = views.staff_remove(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_remove_redirects_to_index_when_user_not_found(self):
        request = DummyRequest(params={"remove": "florp"})

        result = views.staff_remove(request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'


@pytest.fixture
def users(db_session):
    from h import models

    staff = ['agnos', 'bojan', 'cristof']
    nonstaff = ['david', 'eva', 'flora']

    users = {}

    for staff in staff:
        users[staff] = models.User(username=staff,
                                   email=staff + '@example.com',
                                   password='secret',
                                   staff=True)
    for nonstaff in nonstaff:
        users[nonstaff] = models.User(username=nonstaff,
                                      email=nonstaff + '@example.com',
                                      password='secret')

    db_session.add_all(list(users.values()))
    db_session.flush()

    return users


@pytest.fixture()
def routes(config):
    config.add_route('admin_staff', '/adm/staff')
