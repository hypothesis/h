from unittest import mock

import pytest
from pyramid import httpexceptions

from h.views.admin.admins import admins_add, admins_index, admins_remove


@pytest.mark.usefixtures("routes")
class TestAdminsIndex:
    def test_when_no_admins(self, pyramid_request):
        result = admins_index(pyramid_request)

        assert result["admin_users"] == []

    @pytest.mark.usefixtures("users")
    def test_context_contains_admin_usernames(self, pyramid_request):
        result = admins_index(pyramid_request)

        assert set(result["admin_users"]) == {
            "acct:agnos@example.com",
            "acct:bojan@example.com",
            "acct:cristof@foo.org",
        }


@pytest.mark.usefixtures("users", "routes")
class TestAdminsAddRemove:
    def test_add_makes_users_admins(self, pyramid_request, users):
        pyramid_request.params = {"add": "eva", "authority": "foo.org"}

        admins_add(pyramid_request)

        assert users["eva"].admin

    def test_add_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {
            "add": "agnos",
            "authority": pyramid_request.default_authority,
        }

        admins_add(pyramid_request)

        assert users["agnos"].admin

    def test_add_strips_spaces(self, pyramid_request, users):
        pyramid_request.params = {"add": "   david   ", "authority": "   example.com  "}

        admins_add(pyramid_request)

        assert users["david"].admin

    def test_add_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {
            "add": "eva",
            "authority": pyramid_request.default_authority,
        }

        result = admins_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/admins"

    def test_add_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {
            "add": "florp",
            "authority": pyramid_request.default_authority,
        }

        result = admins_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/admins"

    def test_add_flashes_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {
            "add": "florp",
            "authority": pyramid_request.default_authority,
        }
        pyramid_request.session.flash = mock.Mock()

        admins_add(pyramid_request)

        assert pyramid_request.session.flash.call_count == 1

    def test_remove_makes_users_not_admins(self, pyramid_request, users):
        pyramid_request.params = {"remove": "acct:cristof@foo.org"}

        admins_remove(pyramid_request)

        assert not users["cristof"].admin

    def test_remove_is_idempotent(self, pyramid_request, users):
        pyramid_request.params = {"remove": "acct:eva@example.com"}

        admins_remove(pyramid_request)

        assert not users["eva"].admin

    def test_remove_will_not_remove_last_admin(self, pyramid_request, users):
        pyramid_request.params = {"remove": "acct:cristof@foo.org"}
        admins_remove(pyramid_request)
        pyramid_request.params = {"remove": "acct:bojan@example.com"}
        admins_remove(pyramid_request)
        pyramid_request.params = {"remove": "acct:agnos@example.com"}
        admins_remove(pyramid_request)

        assert users["agnos"].admin

    def test_remove_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"remove": "acct:agnos@example.com"}

        result = admins_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/admins"

    def test_remove_redirects_to_index_when_user_not_found(self, pyramid_request):
        pyramid_request.params = {"remove": "acct:florp@example.com"}

        result = admins_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/admins"


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.admins", "/adm/admins")


@pytest.fixture
def users(db_session, factories):
    users = {
        "agnos": factories.User(username="agnos", authority="example.com", admin=True),
        "bojan": factories.User(username="bojan", authority="example.com", admin=True),
        "cristof": factories.User(username="cristof", authority="foo.org", admin=True),
        "david": factories.User(username="david", authority="example.com", admin=False),
        "eva": factories.User(username="eva", authority="foo.org", admin=False),
        "flora": factories.User(username="flora", authority="foo.org", admin=False),
    }

    db_session.flush()

    return users
