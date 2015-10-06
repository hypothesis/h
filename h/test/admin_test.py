# -*- coding: utf-8 -*-
from mock import Mock
from mock import patch
import pytest

from pyramid.testing import DummyRequest
from pyramid import httpexceptions

from h import accounts
from h import admin


class DummyFeature(object):
    def __init__(self, name):
        self.name = name
        self.everyone = False
        self.admins = False
        self.staff = False


features_save_fixtures = pytest.mark.usefixtures('Feature',
                                                 'check_csrf_token',
                                                 'routes_mapper')


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_on(Feature):
    foo = DummyFeature(name='foo')
    bar = DummyFeature(name='bar')
    Feature.all.return_value = [foo, bar]
    request = DummyRequest(post={'foo[everyone]': 'on',
                                 'foo[staff]': 'on',
                                 'bar[admins]': 'on'})

    admin.features_save(request)

    assert foo.everyone == foo.staff == bar.admins == True


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_off(Feature):
    foo = DummyFeature(name='foo')
    foo.everyone = True
    foo.staff = True
    Feature.all.return_value = [foo]
    request = DummyRequest(post={})

    admin.features_save(request)

    assert foo.everyone == foo.staff == False


@features_save_fixtures
def test_features_save_ignores_unknown_fields(Feature):
    foo = DummyFeature(name='foo')
    Feature.all.return_value = [foo]
    request = DummyRequest(post={'foo[wibble]': 'on',
                                 'foo[admins]': 'ignoreme'})

    admin.features_save(request)

    assert foo.admins == False


@features_save_fixtures
def test_features_save_checks_csrf_token(Feature, check_csrf_token):
    Feature.all.return_value = []
    request = DummyRequest(post={})

    admin.features_save(request)

    check_csrf_token.assert_called_with(request)


# The fixtures required to mock all of nipsa_index()'s dependencies.
nipsa_index_fixtures = pytest.mark.usefixtures('nipsa')


@nipsa_index_fixtures
def test_nipsa_index_with_no_nipsad_users(nipsa):
    nipsa.index.return_value = []

    assert admin.nipsa_index(DummyRequest()) == {"userids": []}


@nipsa_index_fixtures
def test_nipsa_index_with_one_nipsad_users(nipsa):
    nipsa.index.return_value = ["acct:kiki@hypothes.is"]

    assert admin.nipsa_index(DummyRequest()) == {"userids": ["kiki"]}


@nipsa_index_fixtures
def test_nipsa_index_with_multiple_nipsad_users(nipsa):
    nipsa.index.return_value = [
        "acct:kiki@hypothes.is", "acct:ursula@hypothes.is",
        "acct:osono@hypothes.is"]

    assert admin.nipsa_index(DummyRequest()) == {
        "userids": ["kiki", "ursula", "osono"]}


# The fixtures required to mock all of nipsa_add()'s dependencies.
nipsa_add_fixtures = pytest.mark.usefixtures('nipsa', 'nipsa_index')


@nipsa_add_fixtures
def test_nipsa_add_calls_nipsa_api_with_userid(nipsa):
    request = DummyRequest(params={"add": "kiki"})

    admin.nipsa_add(request)

    nipsa.add_nipsa.assert_called_once_with(
        request, "acct:kiki@example.com")


@nipsa_add_fixtures
def test_nipsa_add_returns_index(nipsa_index):
    request = DummyRequest(params={"add": "kiki"})
    nipsa_index.return_value = "Keine Bange!"

    assert admin.nipsa_add(request) == "Keine Bange!"


# The fixtures required to mock all of nipsa_remove()'s dependencies.
nipsa_remove_fixtures = pytest.mark.usefixtures('nipsa')


@nipsa_remove_fixtures
def test_nipsa_remove_calls_nipsa_api_with_userid(nipsa):
    request = Mock(params={"remove": "kiki"}, domain="hypothes.is")

    admin.nipsa_remove(request)

    nipsa.remove_nipsa.assert_called_once_with(
        request, "acct:kiki@hypothes.is")


@nipsa_remove_fixtures
def test_nipsa_remove_redirects_to_index():
    request = Mock(params={"remove": "kiki"},
                   domain="hypothes.is",
                   route_url=Mock(return_value="/nipsa"))

    response = admin.nipsa_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)
    assert response.location == "/nipsa"


# The fixtures required to mock all of admins_index()'s dependencies.
admins_index_fixtures = pytest.mark.usefixtures('User')


@admins_index_fixtures
def test_admins_index_when_no_admins(User):
    request = DummyRequest()
    User.admins.return_value = []

    result = admin.admins_index(request)

    assert result["admin_users"] == []


@admins_index_fixtures
def test_admins_index_when_one_admin(User):
    request = DummyRequest()
    User.admins.return_value = [Mock(username="fred")]

    result = admin.admins_index(request)

    assert result["admin_users"] == ["fred"]


@admins_index_fixtures
def test_admins_index_when_multiple_admins(User):
    request = DummyRequest()
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]

    result = admin.admins_index(request)

    assert result["admin_users"] == ["fred", "bob", "frank"]


# The fixtures required to mock all of admins_add()'s dependencies.
admins_add_fixtures = pytest.mark.usefixtures('make_admin', 'admins_index')


@admins_add_fixtures
def test_admins_add_when_no_add_param():
    """It should 404 if the request has no "add" param."""
    with pytest.raises(httpexceptions.HTTPNotFound):
        admin.admins_add(DummyRequest())


@admins_add_fixtures
def test_admins_add_calls_make_admin(make_admin):
    request = DummyRequest(params={"add": "seanh"})

    admin.admins_add(request)

    make_admin.assert_called_once_with("seanh")


@admins_add_fixtures
def test_admins_add_returns_index_on_success(admins_index):
    request = DummyRequest(params={"add": "seanh"})
    admins_index.return_value = "expected data"

    result = admin.admins_add(request)

    assert result == "expected data"


@admins_add_fixtures
def test_admins_add_flashes_on_NoSuchUserError(make_admin):
    make_admin.side_effect = accounts.NoSuchUserError
    request = DummyRequest(params={"add": "seanh"})
    request.session.flash = Mock()

    admin.admins_add(request)

    assert request.session.flash.call_count == 1


@admins_add_fixtures
def test_admins_add_returns_index_on_NoSuchUserError(make_admin, admins_index):
    make_admin.side_effect = accounts.NoSuchUserError
    admins_index.return_value = "expected data"
    request = DummyRequest(params={"add": "seanh"})

    result = admin.admins_add(request)

    assert result == "expected data"


# The fixtures required to mock all of admins_remove()'s dependencies.
admins_remove_fixtures = pytest.mark.usefixtures('User')


@admins_remove_fixtures
def test_admins_remove_calls_get_by_username(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    admin.admins_remove(request)

    User.get_by_username.assert_called_once_with("fred")


@admins_remove_fixtures
def test_admins_remove_sets_admin_to_False(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()
    user = Mock(admin=True)
    User.get_by_username.return_value = user

    admin.admins_remove(request)

    assert user.admin is False


@admins_remove_fixtures
def test_admins_remove_returns_redirect_on_success(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    response = admin.admins_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


@admins_remove_fixtures
def test_admins_remove_404s_if_no_remove_param(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]

    with pytest.raises(httpexceptions.HTTPNotFound):
        admin.admins_remove(DummyRequest())


@admins_remove_fixtures
def test_admins_remove_returns_redirect_when_too_few_admins(User):
    User.admins.return_value = [Mock(username="fred")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    response = admin.admins_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


@admins_remove_fixtures
def test_admins_remove_does_not_delete_last_admin(User):
    User.admins.return_value = [Mock(username="fred")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()
    user = Mock(admin=True)
    User.get_by_username.return_value = user

    admin.admins_remove(request)

    assert user.admin is True


# The fixtures required to mock all of staff_index()'s dependencies.
staff_index_fixtures = pytest.mark.usefixtures('User')


@staff_index_fixtures
def test_staff_index_when_no_staff(User):
    request = DummyRequest()
    User.staff_members.return_value = []

    result = admin.staff_index(request)

    assert result["staff"] == []


@staff_index_fixtures
def test_staff_index_when_one_staff(User):
    request = DummyRequest()
    User.staff_members.return_value = [Mock(username="fred")]

    result = admin.staff_index(request)

    assert result["staff"] == ["fred"]


@staff_index_fixtures
def test_staff_index_when_multiple_staff(User):
    request = DummyRequest()
    User.staff_members.return_value = [Mock(username="fred"),
                                       Mock(username="bob"),
                                       Mock(username="frank")]

    result = admin.staff_index(request)

    assert result["staff"] == ["fred", "bob", "frank"]


# The fixtures required to mock all of staff_add()'s dependencies.
staff_add_fixtures = pytest.mark.usefixtures('make_staff', 'staff_index')


@staff_add_fixtures
def test_staff_add_when_no_add_param():
    """It should 404 if the request has no "add" param."""
    with pytest.raises(httpexceptions.HTTPNotFound):
        admin.staff_add(DummyRequest())


@staff_add_fixtures
def test_staff_add_calls_make_staff(make_staff):
    request = DummyRequest(params={"add": "seanh"})

    admin.staff_add(request)

    make_staff.assert_called_once_with("seanh")


@staff_add_fixtures
def test_staff_add_returns_index_on_success(staff_index):
    request = DummyRequest(params={"add": "seanh"})
    staff_index.return_value = "expected data"

    result = admin.staff_add(request)

    assert result == "expected data"


@staff_add_fixtures
def test_staff_add_flashes_on_NoSuchUserError(make_staff):
    make_staff.side_effect = accounts.NoSuchUserError
    request = DummyRequest(params={"add": "seanh"})
    request.session.flash = Mock()

    admin.staff_add(request)

    assert request.session.flash.call_count == 1


@staff_add_fixtures
def test_staff_add_returns_index_on_NoSuchUserError(make_staff, staff_index):
    make_staff.side_effect = accounts.NoSuchUserError
    staff_index.return_value = "expected data"
    request = DummyRequest(params={"add": "seanh"})

    result = admin.staff_add(request)

    assert result == "expected data"


# The fixtures required to mock all of staff_remove()'s dependencies.
staff_remove_fixtures = pytest.mark.usefixtures('User')


@staff_remove_fixtures
def test_staff_remove_calls_get_by_username(User):
    User.staff_members.return_value = [Mock(username="fred"),
                                       Mock(username="bob"),
                                       Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    admin.staff_remove(request)

    User.get_by_username.assert_called_once_with("fred")


@staff_remove_fixtures
def test_staff_remove_sets_staff_to_False(User):
    User.staff_members.return_value = [Mock(username="fred"),
                                       Mock(username="bob"),
                                       Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()
    user = Mock(staff=True)
    User.get_by_username.return_value = user

    admin.staff_remove(request)

    assert user.staff is False


@staff_remove_fixtures
def test_staff_remove_returns_redirect_on_success(User):
    User.admins.return_value = [Mock(username="fred"),
                                Mock(username="bob"),
                                Mock(username="frank")]
    request = DummyRequest(params={"remove": "fred"})
    request.route_url = Mock()

    response = admin.admins_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


@staff_remove_fixtures
def test_staff_remove_404s_if_no_remove_param():
    with pytest.raises(httpexceptions.HTTPNotFound):
        admin.staff_remove(DummyRequest())


users_index_fixtures = pytest.mark.usefixtures('User')


@users_index_fixtures
def test_users_index():
    request = DummyRequest()

    result = admin.users_index(request)

    assert result == {"username": None, "user": None}


@users_index_fixtures
def test_users_index_looks_up_users_by_username(User):
    request = DummyRequest(params={"username": "bob"})

    result = admin.users_index(request)

    User.get_by_username.assert_called_with("bob")


@users_index_fixtures
def test_users_index_no_user_found(User):
    request = DummyRequest(params={"username": "bob"})
    User.get_by_username.return_value = None

    result = admin.users_index(request)

    assert result == {"username": "bob", "user": None}


@users_index_fixtures
def test_users_index_user_found(User):
    request = DummyRequest(params={"username": "bob"})

    result = admin.users_index(request)

    assert result == {"username": "bob",
                      "user": User.get_by_username.return_value}


badge_index_fixtures = pytest.mark.usefixtures('models')


@badge_index_fixtures
def test_badge_index_returns_all_blocklisted_urls(models):
    assert admin.badge_index(Mock()) == {
        "uris": models.Blocklist.all.return_value}


badge_add_fixtures = pytest.mark.usefixtures('models', 'badge_index')


@badge_add_fixtures
def test_badge_add_adds_uri_to_model(models):
    request = Mock(params={'add': 'test_uri'})

    admin.badge_add(request)

    models.Blocklist.assert_called_once_with(uri='test_uri')
    request.db.add.assert_called_once_with(models.Blocklist.return_value)


@badge_add_fixtures
def test_badge_add_returns_index(badge_index):
    request = Mock(params={'add': 'test_uri'})

    assert admin.badge_add(request) == badge_index.return_value


@badge_add_fixtures
def test_badge_add_flashes_error_if_uri_already_blocked(models):
    request = Mock(params={'add': 'test_uri'})
    models.Blocklist.side_effect = ValueError("test_error_message")

    admin.badge_add(request)

    assert not request.db.add.called
    request.session.flash.assert_called_once_with(
        "test_error_message", "error")


@badge_add_fixtures
def test_badge_add_returns_index_if_uri_already_blocked(models, badge_index):
    request = Mock(params={'add': 'test_uri'})
    models.Blocklist.side_effect = ValueError("test_error_message")

    assert admin.badge_add(request) == badge_index.return_value


badge_remove_fixtures = pytest.mark.usefixtures('models', 'badge_index')


@badge_remove_fixtures
def test_badge_remove_deletes_model(models):
    request = Mock(params={'remove': 'test_uri'})

    admin.badge_remove(request)

    models.Blocklist.get_by_uri.assert_called_once_with('test_uri')
    request.db.delete.assert_called_once_with(
        models.Blocklist.get_by_uri.return_value)


@badge_remove_fixtures
def test_badge_remove_returns_index(badge_index):
    assert admin.badge_remove(Mock(params={'remove': 'test_uri'})) == (
        badge_index.return_value)


@pytest.fixture
def models(request):
    patcher = patch('h.admin.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def badge_index(request):
    patcher = patch('h.admin.badge_index', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def Feature(request):
    patcher = patch('h.models.Feature', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def check_csrf_token(request):
    patcher = patch('pyramid.session.check_csrf_token', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def nipsa(config, request):  # pylint:disable=unused-argument
    patcher = patch('h.admin.nipsa', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def nipsa_index(config, request):  # pylint:disable=unused-argument
    patcher = patch('h.admin.nipsa_index', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def User(config, request):  # pylint:disable=unused-argument
    patcher = patch('h.admin.models.User', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def make_admin(config, request):  # pylint:disable=unused-argument
    patcher = patch('h.admin.accounts.make_admin', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def make_staff(config, request):  # pylint:disable=unused-argument
    patcher = patch('h.admin.accounts.make_staff', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def admins_index(config, request):  # pylint:disable=unused-argument
    patcher = patch('h.admin.admins_index', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def staff_index(config, request):  # pylint:disable=unused-argument
    patcher = patch('h.admin.staff_index', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
