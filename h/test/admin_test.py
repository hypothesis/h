from mock import Mock
from mock import patch
import pytest

from pyramid.testing import DummyRequest
from pyramid import httpexceptions

from h import accounts
from h import admin


@patch("h.admin.nipsa")
def test_nipsa_index_with_no_nipsad_users(nipsa_api):
    nipsa_api.index.return_value = []

    assert admin.nipsa_index(DummyRequest()) == {"userids": []}


@patch("h.admin.nipsa")
def test_index_with_one_nipsad_users(nipsa_api):
    nipsa_api.index.return_value = ["acct:kiki@hypothes.is"]

    assert admin.nipsa_index(DummyRequest()) == {"userids": ["kiki"]}


@patch("h.admin.nipsa")
def test_index_with_multiple_nipsad_users(nipsa_api):
    nipsa_api.index.return_value = [
        "acct:kiki@hypothes.is", "acct:ursula@hypothes.is",
        "acct:osono@hypothes.is"]

    assert admin.nipsa_index(DummyRequest()) == {
        "userids": ["kiki", "ursula", "osono"]}


@patch("h.admin.nipsa")
def test_nipsa_add_calls_nipsa_api_with_userid(nipsa_api):
    request = DummyRequest(params={"add": "kiki"})

    admin.nipsa_add(request)

    nipsa_api.add_nipsa.assert_called_once_with(
        request, "acct:kiki@example.com")


@patch("h.admin.nipsa_index")
@patch("h.admin.nipsa")
def test_nipsa_add_returns_index(nipsa_api, index):
    request = DummyRequest(params={"add": "kiki"})
    index.return_value = "Keine Bange!"

    assert admin.nipsa_add(request) == "Keine Bange!"


@patch("h.admin.nipsa")
def test_nipsa_remove_calls_nipsa_api_with_userid(nipsa_api):
    request = Mock(params={"remove": "kiki"}, domain="hypothes.is")

    admin.nipsa_remove(request)

    nipsa_api.remove_nipsa.assert_called_once_with(
        request, "acct:kiki@hypothes.is")


@patch("h.admin.nipsa")
def test_nipsa_remove_redirects_to_index(nipsa_api):
    request = Mock(params={"remove": "kiki"},
                   domain="hypothes.is",
                   route_url=Mock(return_value="/nipsa"))

    response = admin.nipsa_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)
    assert response.location == "/nipsa"


def test_admins_index_when_no_admins(user_model):
    request = DummyRequest()
    user_model.admins.return_value = []

    result = admin.admins_index(request)

    assert result["admin_users"] == []


def test_admins_index_when_one_admin(user_model):
    request = DummyRequest()
    user_model.admins.return_value = [Mock(username="fred")]

    result = admin.admins_index(request)

    assert result["admin_users"] == ["fred"]


def test_admins_index_when_multiple_admins(user_model):
    request = DummyRequest()
    user_model.admins.return_value = [Mock(username="fred"),
                                      Mock(username="bob"),
                                      Mock(username="frank")]

    result = admin.admins_index(request)

    assert result["admin_users"] == ["fred", "bob", "frank"]


def test_admins_add_when_no_add_param():
    """create() should 404 if the request has no "add" param."""
    with pytest.raises(httpexceptions.HTTPNotFound):
        admin.admins_add(DummyRequest())


@patch("h.accounts.make_admin")
@pytest.mark.usefixtures("user_model")
def test_admins_add_calls_make_admin(make_admin):
    request = DummyRequest(params={"add": "seanh"})

    admin.admins_add(request)

    make_admin.assert_called_once_with("seanh")


@patch("h.admin.admins_index")
@patch("h.accounts.make_admin")
@pytest.mark.usefixtures("user_model")
def test_admins_add_returns_index_on_success(make_admin, index):
    request = DummyRequest(params={"add": "seanh"})
    index.return_value = "expected data"

    result = admin.admins_add(request)

    assert result == "expected data"


@patch("h.accounts.make_admin")
@pytest.mark.usefixtures("user_model")
def test_admins_add_flashes_on_NoSuchUserError(make_admin):
    make_admin.side_effect = accounts.NoSuchUserError
    request = DummyRequest(params={"add": "seanh"})
    request.session.flash = Mock()

    admin.admins_add(request)

    assert request.session.flash.call_count == 1


@patch("h.admin.admins_index")
@patch("h.accounts.make_admin")
@pytest.mark.usefixtures("user_model")
def test_admins_add_returns_index_on_NoSuchUserError(make_admin, index):
    make_admin.side_effect = accounts.NoSuchUserError
    index.return_value = "expected data"
    request = DummyRequest(params={"add": "seanh"})

    result = admin.admins_add(request)

    assert result == "expected data"


def test_admins_remove_calls_get_by_username(user_model):
    user_model.admins.return_value = [Mock(username="fred"),
                                      Mock(username="bob"),
                                      Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    admin.admins_remove(request)

    user_model.get_by_username.assert_called_once_with("fred")


def test_admis_remove_sets_admin_to_False(user_model):
    user_model.admins.return_value = [Mock(username="fred"),
                                      Mock(username="bob"),
                                      Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()
    user = Mock(admin=True)
    user_model.get_by_username.return_value = user

    admin.admins_remove(request)

    assert user.admin is False


def test_admin_delete_returns_redirect_on_success(user_model):
    user_model.admins.return_value = [Mock(username="fred"),
                                      Mock(username="bob"),
                                      Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    response = admin.admins_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


def test_admin_delete_404s_if_no_remove_param(user_model):
    user_model.admins.return_value = [Mock(username="fred"),
                                      Mock(username="bob"),
                                      Mock(username="frank")]

    with pytest.raises(httpexceptions.HTTPNotFound):
        admin.admins_remove(DummyRequest())


def test_admin_delete_returns_redirect_when_too_few_admins(user_model):
    user_model.admins.return_value = [Mock(username="fred")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    response = admin.admins_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


def test_admin_delete_does_not_delete_last_admin(user_model):
    user_model.admins.return_value = [Mock(username="fred")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()
    user = Mock(admin=True)
    user_model.get_by_username.return_value = user

    admin.admins_remove(request)

    assert user.admin is True


@pytest.fixture
def user_model(config, request):
    patcher = patch('h.admin.models.User', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
