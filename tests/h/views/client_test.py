# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from pyramid.httpexceptions import HTTPFound
import pytest

from h.views import client
from h import __version__


def test_annotator_token_calls_generate_jwt(generate_jwt, pyramid_request):
    client.annotator_token(pyramid_request)

    generate_jwt.assert_called_once_with(pyramid_request, 3600)


def test_annotator_token_returns_token(generate_jwt, pyramid_request):
    result = client.annotator_token(pyramid_request)

    assert result == generate_jwt.return_value


@pytest.mark.usefixtures('routes', 'pyramid_settings')
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
                'googleAnalytics': 'UA-4567',
                'oauthAuthorizeUrl': 'http://example.com/oauth/authorize',
                'oauthRevokeUrl': 'http://example.com/oauth/revoke',
                'oauthClientId': 'test-client-id',
                'oauthEnabled': True,
                }

        actual_config = json.loads(ctx['app_config'])

        assert actual_config == expected_config

    def test_it_sets_embed_url(self, pyramid_request):
        ctx = client.sidebar_app(pyramid_request)

        assert ctx['embed_url'] == '/embed.js'

    def test_it_disables_oauth(self, pyramid_request):
        pyramid_request.feature.flags['client_oauth'] = False

        ctx = client.sidebar_app(pyramid_request)
        cfg = json.loads(ctx['app_config'])

        assert cfg['oauthEnabled'] is False


@pytest.mark.usefixtures('routes', 'pyramid_settings')
class TestEmbedRedirect(object):
    def test_redirects_to_client_boot_script(self, pyramid_request):
        pyramid_request.feature.flags['embed_cachebuster'] = False

        rsp = client.embed_redirect(pyramid_request)

        assert isinstance(rsp, HTTPFound)
        assert rsp.location == 'https://cdn.hypothes.is/hypothesis'

    def test_adds_cachebuster(self, pyramid_request):
        pyramid_request.feature.flags['embed_cachebuster'] = True

        rsp = client.embed_redirect(pyramid_request)

        assert isinstance(rsp, HTTPFound)
        assert '?cachebuster=' in rsp.location


@pytest.fixture
def pyramid_settings(pyramid_settings):

    pyramid_settings.update({
        'ga_client_tracking_id': 'UA-4567',
        'h.client_oauth_id': 'test-client-id',
        'h.sentry_dsn_client': 'test-sentry-dsn',
        'h.websocket_url': 'wss://example.com/ws',
        'authority': 'example.com'
        })

    return pyramid_settings


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('api.index', '/api')
    pyramid_config.add_route('embed', '/embed.js')
    pyramid_config.add_route('index', '/')
    pyramid_config.add_route('sidebar_app', '/app.html')
    pyramid_config.add_route('oauth_authorize', '/oauth/authorize')
    pyramid_config.add_route('oauth_revoke', '/oauth/revoke')


@pytest.fixture
def generate_jwt(patch):
    func = patch('h.views.client.generate_jwt')
    func.return_value = 'abc123'
    return func
