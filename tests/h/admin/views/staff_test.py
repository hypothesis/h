# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from pyramid import httpexceptions
from pyramid.testing import DummyRequest
import pytest

from h.admin.views import staff as views


@pytest.mark.usefixtures('routes')
class TestStaffIndex(object):
    def test_when_no_staff(self, req):
        result = views.staff_index(req)

        assert result["staff"] == []

    @pytest.mark.usefixtures('users')
    def test_context_contains_staff_usernames(self, req):
        result = views.staff_index(req)

        assert set(result["staff"]) == set(["agnos", "bojan", "cristof"])


@pytest.mark.usefixtures('users', 'routes')
class TestStaffAddRemove(object):

    def test_add_makes_users_staff(self, req, users):
        req.params = {"add": "eva"}

        views.staff_add(req)

        assert users['eva'].staff

    def test_add_is_idempotent(self, req, users):
        req.params = {"add": "agnos"}

        views.staff_add(req)

        assert users['agnos'].staff

    def test_add_redirects_to_index(self, req):
        req.params = {"add": "eva"}

        result = views.staff_add(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_add_redirects_to_index_when_user_not_found(self, req):
        req.params = {"add": "florp"}

        result = views.staff_add(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_add_flashes_when_user_not_found(self, req):
        req.params = {"add": "florp"}
        req.session.flash = mock.Mock()

        views.staff_add(req)

        assert req.session.flash.call_count == 1

    def test_remove_makes_users_not_staff(self, req, users):
        req.params = {"remove": "cristof"}

        views.staff_remove(req)

        assert not users['cristof'].staff

    def test_remove_is_idempotent(self, req, users):
        req.params = {"remove": "eva"}

        views.staff_remove(req)

        assert not users['eva'].staff

    def test_remove_redirects_to_index(self, req):
        req.params = {"remove": "agnos"}

        result = views.staff_remove(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'

    def test_remove_redirects_to_index_when_user_not_found(self, req):
        req.params = {"remove": "florp"}

        result = views.staff_remove(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/staff'


@pytest.fixture
def req(db_session):
    return DummyRequest(db=db_session)


@pytest.fixture
def routes(config):
    config.add_route('admin_staff', '/adm/staff')


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
