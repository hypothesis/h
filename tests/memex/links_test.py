# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from memex.links import LinksService
from memex.links import add_annotation_link_generator
from memex.links import links_factory


class TestLinksService(object):
    def test_get_returns_link_text(self, registry):
        svc = LinksService(base_url='http://example.com', registry=registry)

        result = svc.get(mock.sentinel.annotation, 'giraffe')

        assert result == 'http://giraffes.com'

    def test_get_returns_link_text_for_hidden_links(self, registry):
        svc = LinksService(base_url='http://example.com', registry=registry)

        result = svc.get(mock.sentinel.annotation, 'kiwi')

        assert result == 'http://kiwi.net'

    def test_get_passes_generators_request_with_base_url(self, registry):
        svc = LinksService(base_url='http://donkeys.com', registry=registry)

        result = svc.get(mock.sentinel.annotation, 'namedroute')

        assert result == 'http://donkeys.com/some/path'

    def test_get_passes_generators_annotation(self, registry):
        annotation = mock.Mock(id=12345)
        svc = LinksService(base_url='http://example.com', registry=registry)

        result = svc.get(annotation, 'paramroute')

        assert result == 'http://example.com/annotations/12345'

    def test_get_all_includes_nonhidden_links(self, registry):
        svc = LinksService(base_url='http://example.com', registry=registry)

        result = svc.get_all(mock.sentinel.annotation)

        assert result['giraffe'] == 'http://giraffes.com'
        assert result['elephant'] == 'https://elephant.org'

    def test_get_all_does_not_include_hidden_links(self, registry):
        svc = LinksService(base_url='http://example.com', registry=registry)

        result = svc.get_all(mock.sentinel.annotation)

        assert 'kiwi' not in result

    def test_get_all_does_not_include_links_returning_none(self, registry):
        svc = LinksService(base_url='http://example.com', registry=registry)

        result = svc.get_all(mock.sentinel.annotation)

        assert 'returnsnone' not in result


class TestLinksFactory(object):
    def test_returns_links_service(self, pyramid_request):
        svc = links_factory(None, pyramid_request)

        assert isinstance(svc, LinksService)

    def test_base_url_is_development_base_if_not_set(self, pyramid_request):
        svc = links_factory(None, pyramid_request)

        assert svc.base_url == 'http://localhost:5000'

    def test_base_url_is_app_url_setting_if_set(self, pyramid_request):
        pyramid_request.registry.settings['h.app_url'] = 'https://hypothes.is'

        svc = links_factory(None, pyramid_request)

        assert svc.base_url == 'https://hypothes.is'

    def test_registry_is_request_registry(self, pyramid_request):
        svc = links_factory(None, pyramid_request)

        assert svc.registry == pyramid_request.registry


@pytest.fixture
def registry(pyramid_config):
    pyramid_config.add_route('some.named.route', '/some/path')
    pyramid_config.add_route('param.route', '/annotations/{id}')

    registry = pyramid_config.registry

    add_annotation_link_generator(registry,
                                  'giraffe',
                                  lambda r, a: 'http://giraffes.com')
    add_annotation_link_generator(registry,
                                  'elephant',
                                  lambda r, a: 'https://elephant.org')
    add_annotation_link_generator(registry,
                                  'kiwi',
                                  lambda r, a: 'http://kiwi.net',
                                  hidden=True)
    add_annotation_link_generator(registry,
                                  'returnsnone',
                                  lambda r, a: None)
    add_annotation_link_generator(registry,
                                  'namedroute',
                                  lambda r, a: r.route_url('some.named.route'))
    add_annotation_link_generator(registry,
                                  'paramroute',
                                  lambda r, a: r.route_url('param.route', id=a.id),
                                  hidden=True)

    return registry
