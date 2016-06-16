# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.request import apply_request_extensions
import pytest

from h.admin.views import nipsa as views


@pytest.mark.usefixtures('nipsa_service', 'routes')
class TestNipsaIndex(object):
    def test_lists_flagged_usernames(self, pyramid_request):
        result = views.nipsa_index(pyramid_request)

        assert set(result['usernames']) == set(['kiki', 'ursula', 'osono'])

    def test_lists_flagged_usernames_no_results(self, nipsa_service, pyramid_request):
        nipsa_service.flagged = set([])

        result = views.nipsa_index(pyramid_request)

        assert result['usernames'] == []


@pytest.mark.usefixtures('nipsa_service', 'routes')
class TestNipsaAddRemove(object):
    def test_add_flags_user(self, nipsa_service, pyramid_request):
        pyramid_request.params = {"add": "carl"}

        views.nipsa_add(pyramid_request)

        assert 'acct:carl@example.com' in nipsa_service.flagged

    def test_add_ignores_empty_user(self, nipsa_service, pyramid_request):
        pyramid_request.params = {"add": ""}

        views.nipsa_add(pyramid_request)

        assert 'acct:@example.com' not in nipsa_service.flagged

    def test_add_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"add": "carl"}

        result = views.nipsa_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == '/adm/nipsa'

    def test_remove_unflags_user(self, nipsa_service, pyramid_request):
        pyramid_request.params = {"remove": "kiki"}

        views.nipsa_remove(pyramid_request)

        assert 'acct:kiki@example.com' not in nipsa_service.flagged

    def test_remove_ignores_empty_user(self, nipsa_service, pyramid_request):
        # Add this bogus userid just to make sure it doesn't get removed.
        nipsa_service.flagged.add('acct:@example.com')
        pyramid_request.params = {"remove": ""}

        views.nipsa_remove(pyramid_request)

        assert 'acct:@example.com' in nipsa_service.flagged

    def test_remove_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"remove": "kiki"}

        result = views.nipsa_remove(pyramid_request)

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
def nipsa_service(pyramid_config, pyramid_request):
    service = FakeNipsaService()

    pyramid_config.include('pyramid_services')
    pyramid_config.register_service(service, name='nipsa')

    apply_request_extensions(pyramid_request)

    return service


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('admin_nipsa', '/adm/nipsa')
