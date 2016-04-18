# -*- coding: utf-8 -*-

from mock import Mock
from pyramid import httpexceptions
from pyramid.testing import DummyRequest
import pytest

from h import accounts
from h.admin.views import staff as views


# The fixtures required to mock all of staff_index()'s dependencies.
staff_index_fixtures = pytest.mark.usefixtures('User')


@staff_index_fixtures
def test_staff_index_when_no_staff(User):
    request = DummyRequest()
    User.staff_members.return_value = []

    result = views.staff_index(request)

    assert result["staff"] == []


@staff_index_fixtures
def test_staff_index_when_one_staff(User):
    request = DummyRequest()
    User.staff_members.return_value = [Mock(username="fred")]

    result = views.staff_index(request)

    assert result["staff"] == ["fred"]


@staff_index_fixtures
def test_staff_index_when_multiple_staff(User):
    request = DummyRequest()
    User.staff_members.return_value = [Mock(username="fred"),
                                       Mock(username="bob"),
                                       Mock(username="frank")]

    result = views.staff_index(request)

    assert result["staff"] == ["fred", "bob", "frank"]


# The fixtures required to mock all of staff_add()'s dependencies.
staff_add_fixtures = pytest.mark.usefixtures('make_staff', 'staff_index')


@staff_add_fixtures
def test_staff_add_calls_make_staff(make_staff):
    request = DummyRequest(params={"add": "seanh"})

    views.staff_add(request)

    make_staff.assert_called_once_with("seanh")


@staff_add_fixtures
def test_staff_add_returns_index_on_success(staff_index):
    request = DummyRequest(params={"add": "seanh"})
    staff_index.return_value = "expected data"

    result = views.staff_add(request)

    assert result == "expected data"


@staff_add_fixtures
def test_staff_add_flashes_on_NoSuchUserError(make_staff):
    make_staff.side_effect = accounts.NoSuchUserError
    request = DummyRequest(params={"add": "seanh"})
    request.session.flash = Mock()

    views.staff_add(request)

    assert request.session.flash.call_count == 1


@staff_add_fixtures
def test_staff_add_returns_index_on_NoSuchUserError(make_staff, staff_index):
    make_staff.side_effect = accounts.NoSuchUserError
    staff_index.return_value = "expected data"
    request = DummyRequest(params={"add": "seanh"})

    result = views.staff_add(request)

    assert result == "expected data"


# The fixtures required to mock all of staff_remove()'s dependencies.
staff_remove_fixtures = pytest.mark.usefixtures('User')


@staff_remove_fixtures
def test_staff_remove_calls_get_by_username(User):
    User.staff_members.return_value = [Mock(username="fred"),
                                       Mock(username="bob"),
                                       Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})

    views.staff_remove(request)

    User.get_by_username.assert_called_once_with("fred")


@staff_remove_fixtures
def test_staff_remove_sets_staff_to_False(User):
    User.staff_members.return_value = [Mock(username="fred"),
                                       Mock(username="bob"),
                                       Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    user = Mock(staff=True)
    User.get_by_username.return_value = user

    views.staff_remove(request)

    assert user.staff is False


@staff_remove_fixtures
def test_staff_remove_returns_redirect_on_success(User):
    User.staff_members.return_value = [Mock(username="fred"),
                                       Mock(username="bob"),
                                       Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})

    response = views.staff_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


@pytest.fixture(autouse=True)
def routes(config):
    config.add_route('admin_staff', '/adm/staff')


@pytest.fixture
def User(patch):
    return patch('h.models.User')


@pytest.fixture
def make_staff(patch):
    return patch('h.admin.views.staff.accounts.make_staff')


@pytest.fixture
def staff_index(patch):
    return patch('h.admin.views.staff.staff_index')
