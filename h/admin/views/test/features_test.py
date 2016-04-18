# -*- coding: utf-8 -*-

from pyramid.testing import DummyRequest
import pytest

from h.admin.views import features as views


class DummyFeature(object):
    def __init__(self, name):
        self.name = name
        self.everyone = False
        self.admins = False
        self.staff = False


features_save_fixtures = pytest.mark.usefixtures('Feature',
                                                 'check_csrf_token')


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_on(Feature):
    foo = DummyFeature(name='foo')
    bar = DummyFeature(name='bar')
    Feature.all.return_value = [foo, bar]
    request = DummyRequest(post={'foo[everyone]': 'on',
                                 'foo[staff]': 'on',
                                 'bar[admins]': 'on'})

    views.features_save(request)

    assert foo.everyone == foo.staff == bar.admins == True


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_off(Feature):
    foo = DummyFeature(name='foo')
    foo.everyone = True
    foo.staff = True
    Feature.all.return_value = [foo]
    request = DummyRequest(post={})

    views.features_save(request)

    assert foo.everyone == foo.staff == False


@features_save_fixtures
def test_features_save_ignores_unknown_fields(Feature):
    foo = DummyFeature(name='foo')
    Feature.all.return_value = [foo]
    request = DummyRequest(post={'foo[wibble]': 'on',
                                 'foo[admins]': 'ignoreme'})

    views.features_save(request)

    assert foo.admins == False


@features_save_fixtures
def test_features_save_checks_csrf_token(Feature, check_csrf_token):
    Feature.all.return_value = []
    request = DummyRequest(post={})

    views.features_save(request)

    check_csrf_token.assert_called_with(request)


@pytest.fixture(autouse=True)
def routes(config):
    config.add_route('admin_features', '/adm/features')


@pytest.fixture
def Feature(patch):
    return patch('h.models.Feature')


@pytest.fixture
def check_csrf_token(patch):
    return patch('pyramid.session.check_csrf_token')
