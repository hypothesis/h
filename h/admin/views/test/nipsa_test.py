# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.testing import DummyRequest as _DummyRequest
import pytest

from h.admin.views import nipsa as views


class DummyRequest(_DummyRequest):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auth_domain', 'example.com')
        super(DummyRequest, self).__init__(*args, **kwargs)


# The fixtures required to mock all of nipsa_index()'s dependencies.
nipsa_index_fixtures = pytest.mark.usefixtures('nipsa')


@nipsa_index_fixtures
def test_nipsa_index_with_no_nipsad_users(nipsa):
    nipsa.index.return_value = []

    assert views.nipsa_index(DummyRequest()) == {"usernames": []}


@nipsa_index_fixtures
def test_nipsa_index_with_one_nipsad_users(nipsa):
    nipsa.index.return_value = ["acct:kiki@hypothes.is"]

    assert views.nipsa_index(DummyRequest()) == {"usernames": ["kiki"]}


@nipsa_index_fixtures
def test_nipsa_index_with_multiple_nipsad_users(nipsa):
    nipsa.index.return_value = [
        "acct:kiki@hypothes.is", "acct:ursula@hypothes.is",
        "acct:osono@hypothes.is"]

    assert views.nipsa_index(DummyRequest()) == {
        "usernames": ["kiki", "ursula", "osono"]}


# The fixtures required to mock all of nipsa_add()'s dependencies.
nipsa_add_fixtures = pytest.mark.usefixtures('nipsa', 'nipsa_index')


@nipsa_add_fixtures
def test_nipsa_add_calls_nipsa_api_with_userid(nipsa):
    request = DummyRequest(params={"add": "kiki"})

    views.nipsa_add(request)

    nipsa.add_nipsa.assert_called_once_with(
        request, "acct:kiki@example.com")


@nipsa_add_fixtures
def test_nipsa_add_returns_index(nipsa_index):
    request = DummyRequest(params={"add": "kiki"})
    nipsa_index.return_value = "Keine Bange!"

    assert views.nipsa_add(request) == "Keine Bange!"


# The fixtures required to mock all of nipsa_remove()'s dependencies.
nipsa_remove_fixtures = pytest.mark.usefixtures('nipsa')


@nipsa_remove_fixtures
def test_nipsa_remove_calls_nipsa_api_with_userid(nipsa):
    request = DummyRequest(params={"remove": "kiki"})

    views.nipsa_remove(request)

    nipsa.remove_nipsa.assert_called_once_with(
        request, "acct:kiki@example.com")


@nipsa_remove_fixtures
def test_nipsa_remove_redirects_to_index():
    request = DummyRequest(params={"remove": "kiki"})

    response = views.nipsa_remove(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)


@pytest.fixture(autouse=True)
def routes(config):
    config.add_route('admin_nipsa', '/adm/nipsa')


@pytest.fixture
def nipsa(patch):
    return patch('h.admin.views.nipsa.nipsa')


@pytest.fixture
def nipsa_index(patch):
    return patch('h.admin.views.nipsa.nipsa_index')
