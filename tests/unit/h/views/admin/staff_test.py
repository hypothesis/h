from unittest import mock

import pytest
from pyramid import httpexceptions

from h.views.admin.staff import staff_add, staff_index, staff_remove


@pytest.mark.usefixtures("routes")
class TestStaffIndex:
    def test_when_no_staff(self, pyramid_request):
        result = staff_index(pyramid_request)

        assert result["staff"] == []

    @pytest.mark.usefixtures("users")
    def test_context_contains_staff_usernames(self, pyramid_request):
        result = staff_index(pyramid_request)

        assert set(result["staff"]) == {
            "acct:agnos@example.com",
            "acct:bojan@example.com",
            "acct:cristof@foo.org",
        }


@pytest.mark.usefixtures("users", "routes")
class TestStaffAddRemove:
    def test_add_makes_users_staff(self, pyramid_request, users):
        pyramid_request.params = {"add": "eva", "authority": "foo.org"}

        staff_add(pyramid_request)

        assert users["eva"].staff

    def test_add_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {
            "add": "agnos",
            "authority": pyramid_request.default_authority,
        }

        staff_add(pyramid_request)

        assert users["agnos"].staff

    def test_add_strips_spaces(self, pyramid_request, users):
        pyramid_request.params = {"add": "   eva   ", "authority": "     foo.org   "}

        staff_add(pyramid_request)

        assert users["eva"].staff

    def test_add_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {
            "add": "eva",
            "authority": pyramid_request.default_authority,
        }

        result = staff_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/staff"

    def test_add_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {
            "add": "florp",
            "authority": pyramid_request.default_authority,
        }

        result = staff_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/staff"

    def test_add_flashes_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {
            "add": "florp",
            "authority": pyramid_request.default_authority,
        }
        pyramid_request.session.flash = mock.Mock()

        staff_add(pyramid_request)

        assert pyramid_request.session.flash.call_count == 1

    def test_remove_makes_users_not_staff(self, pyramid_request, users):
        pyramid_request.params = {"remove": "acct:cristof@foo.org"}

        staff_remove(pyramid_request)

        assert not users["cristof"].staff

    def test_remove_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {"remove": "acct:eva@example.com"}

        staff_remove(pyramid_request)

        assert not users["eva"].staff

    def test_remove_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"remove": "acct:agnos@example.com"}

        result = staff_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/staff"

    def test_remove_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"remove": "acct:florp@example.com"}

        result = staff_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/staff"


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.staff", "/adm/staff")


@pytest.fixture
def users(db_session, factories):
    users = {
        "agnos": factories.User(username="agnos", authority="example.com", staff=True),
        "bojan": factories.User(username="bojan", authority="example.com", staff=True),
        "cristof": factories.User(username="cristof", authority="foo.org", staff=True),
        "david": factories.User(username="david", authority="example.com", staff=False),
        "eva": factories.User(username="eva", authority="foo.org", staff=False),
        "flora": factories.User(username="flora", authority="foo.org", staff=False),
    }
    db_session.flush()

    return users
