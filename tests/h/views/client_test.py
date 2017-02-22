# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h._compat import StringIO
import json

from mock import Mock, patch
from pyramid.httpexceptions import HTTPFound
import pytest
import requests

from h.views import client
from h import __version__


def test_annotator_token_calls_generate_jwt(generate_jwt, pyramid_request):
    client.annotator_token(pyramid_request)

    generate_jwt.assert_called_once_with(pyramid_request, 3600)


def test_annotator_token_returns_token(generate_jwt, pyramid_request):
    result = client.annotator_token(pyramid_request)

    assert result == generate_jwt.return_value


@pytest.mark.usefixtures('client_assets_env', 'routes', 'pyramid_settings')
class TestSidebarApp(object):

    def test_it_includes_client_config(self, pyramid_request):
        ctx = client.sidebar_app(pyramid_request)
        expected_config = {
                'apiUrl': 'http://example.com/api',
                'websocketUrl': 'wss://example.com/ws',
                'serviceUrl': 'http://example.com/',
                'release': __version__,
                'raven': {
                    'dsn': 'test-sentry-dsn',
                    'release': __version__
                },
                'authDomain': 'example.com',
                'googleAnalytics': 'UA-4567'
                }

        actual_config = json.loads(ctx['app_config'])

        assert actual_config == expected_config

    def test_it_sets_asset_urls(self, pyramid_request):
        pyramid_request.feature.flags['use_client_boot_script'] = False

        ctx = client.sidebar_app(pyramid_request)

        assert ctx['app_css_urls'] == ['/assets/client/app.css']
        assert ctx['app_js_urls'] == ['/assets/client/app.js']

    def test_uses_client_boot_script_when_enabled(self, pyramid_request):
        pyramid_request.feature.flags['use_client_boot_script'] = True

        ctx = client.sidebar_app(pyramid_request)

        assert ctx['app_js_urls'] == ['/embed.js']
        assert ctx['app_css_urls'] == []


@pytest.mark.usefixtures('client_assets_env', 'routes')
class TestEmbed(object):
    def test_it_sets_asset_urls(self, pyramid_request):
        ctx = client.embed(pyramid_request)
        assert ctx['inject_resource_urls'] == [
            'http://example.com/assets/client/polyfills.js',
            'http://example.com/assets/client/inject.js',
            'http://example.com/assets/client/inject.css',
            ]

    def test_it_sets_content_type(self, pyramid_request):
        client.embed(pyramid_request)
        assert pyramid_request.response.content_type == 'text/javascript'


@pytest.mark.usefixtures('requests_get', 'routes', 'pyramid_settings')
class TestEmbedRedirect(object):
    def test_fetches_client_boot_script(self, pyramid_request, requests_get):
        client.embed_redirect(pyramid_request)
        requests_get.assert_called_with('https://unpkg.com/hypothesis')

    def test_fetches_custom_client_boot_script(self, pyramid_request, requests_get):
        pyramid_request.registry.settings['h.client_url'] = 'https://client.hypothes.is'
        client.embed_redirect(pyramid_request)
        requests_get.assert_called_with('https://client.hypothes.is')

    def test_redirects_to_client_boot_script(self, pyramid_request):
        rsp = client.embed_redirect(pyramid_request)

        assert isinstance(rsp, HTTPFound)
        assert rsp.location == 'https://unpkg.com/hypothesis@0.100'


@pytest.yield_fixture
def requests_get(fake_client_boot_response):
    with patch('h.views.client.requests.get') as requests_get:
        requests_get.return_value = fake_client_boot_response
        yield requests_get


@pytest.fixture
def fake_client_boot_response():
    rsp = requests.models.Response()
    rsp.url = 'https://unpkg.com/hypothesis@0.100'
    rsp.raw = StringIO(b'/* client boot script */')
    rsp.status_code = 200
    return rsp


@pytest.fixture
def client_assets_env(pyramid_config):
    assets_client_env = Mock(spec_set=['urls'])

    bundles = {
        'app_js': ['/assets/client/app.js'],
        'app_css': ['/assets/client/app.css'],
        'inject_js': ['/assets/client/polyfills.js', '/assets/client/inject.js'],
        'inject_css': ['/assets/client/inject.css'],
    }

    def urls(bundle_name):
        return bundles[bundle_name]
    assets_client_env.urls = urls
    pyramid_config.registry['assets_client_env'] = assets_client_env


@pytest.fixture
def pyramid_settings(pyramid_settings):

    pyramid_settings.update({
        'ga_client_tracking_id': 'UA-4567',
        'h.client.sentry_dsn': 'test-sentry-dsn',
        'h.websocket_url': 'wss://example.com/ws',
        'auth_domain': 'example.com'
        })

    return pyramid_settings


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('api.index', '/api')
    pyramid_config.add_route('assets_client', '/assets/client/{subpath}')
    pyramid_config.add_route('embed', '/embed.js')
    pyramid_config.add_route('index', '/')
    pyramid_config.add_route('sidebar_app', '/app.html')


@pytest.fixture
def generate_jwt(patch):
    func = patch('h.views.client.generate_jwt')
    func.return_value = 'abc123'
    return func
