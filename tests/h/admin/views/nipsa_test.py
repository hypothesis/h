# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.request import apply_request_extensions
from pyramid.testing import DummyRequest
import pytest

from h.admin.views import nipsa as views


@pytest.mark.usefixtures('nipsa_service', 'routes')
class TestNipsaIndex(object):
    def test_lists_flagged_usernames(self, req):
        result = views.nipsa_index(req)

        assert set(result['usernames']) == set(['kiki', 'ursula', 'osono'])

    def test_lists_flagged_usernames_no_results(self, nipsa_service, req):
        nipsa_service.flagged = set([])

        result = views.nipsa_index(req)

        assert result['usernames'] == []


@pytest.mark.usefixtures('nipsa_service', 'routes')
class TestNipsaAddRemove(object):
    def test_add_flags_user(self, nipsa_service, req):
        req.params = {"add": "carl"}

        views.nipsa_add(req)

        assert 'acct:carl@example.com' in nipsa_service.flagged

    def test_add_ignores_empty_user(self, nipsa_service, req):
        req.params = {"add": ""}

        views.nipsa_add(req)

        assert 'acct:@example.com' not in nipsa_service.flagged

    def test_add_redirects_to_index(self, req):
        req.params = {"add": "carl"}

        result = views.nipsa_add(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/nipsa'

    def test_remove_unflags_user(self, nipsa_service, req):
        req.params = {"remove": "kiki"}

        views.nipsa_remove(req)

        assert 'acct:kiki@example.com' not in nipsa_service.flagged

    def test_remove_ignores_empty_user(self, nipsa_service, req):
        # Add this bogus userid just to make sure it doesn't get removed.
        nipsa_service.flagged.add('acct:@example.com')
        req.params = {"remove": ""}

        views.nipsa_remove(req)

        assert 'acct:@example.com' in nipsa_service.flagged

    def test_remove_redirects_to_index(self, req):
        req.params = {"remove": "kiki"}

        result = views.nipsa_remove(req)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/nipsa'


class FakeNipsaService(object):
    def __init__(self):
        self.flagged = {'acct:kiki@example.com',
                        'acct:ursula@example.com',
                        'acct:osono@example.com'}

    @property
    def flagged_userids(self):
        return list(self.flagged)

    def flag(self, userid):
        self.flagged.add(userid)

    def unflag(self, userid):
        self.flagged.remove(userid)


@pytest.fixture
def nipsa_service(config):
    service = FakeNipsaService()

    config.include('pyramid_services')
    config.register_service(service, name='nipsa')

    return service


@pytest.fixture
def req():
    request = DummyRequest()
    request.auth_domain = 'example.com'
    apply_request_extensions(request)
    return request


@pytest.fixture
def routes(config):
    config.add_route('admin_nipsa', '/adm/nipsa')
