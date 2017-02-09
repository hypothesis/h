# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock
import pytest

from h.views import client


def test_annotator_token_calls_generate_jwt(generate_jwt, pyramid_request):
    client.annotator_token(pyramid_request)

    generate_jwt.assert_called_once_with(pyramid_request, 3600)


def test_annotator_token_returns_token(generate_jwt, pyramid_request):
    result = client.annotator_token(pyramid_request)

    assert result == generate_jwt.return_value


@pytest.mark.usefixtures('routes')
class TestRenderApp(object):
    def test_uses_client_boot_script(self, pyramid_request_):
        pyramid_request_.feature.flags['use_client_boot_script'] = True
        rsp = client.render_app(pyramid_request_)
        assert '<script src="http://example.com/assets/client/boot.js"></script>' in rsp.text

    def test_does_not_use_client_boot_script_when_disabled(self, pyramid_request_):
        pyramid_request_.feature.flags['use_client_boot_script'] = False
        rsp = client.render_app(pyramid_request_)
        assert '<script src="http://example.com/assets/client/boot.js"></script>' not in rsp.text


@pytest.mark.usefixtures('routes')
class TestEmbed(object):
    def test_uses_client_boot_script(self, pyramid_request_):
        pyramid_request_.feature.flags['use_client_boot_script'] = True
        ctx = client.embed(pyramid_request_)
        assert ctx['client_boot_url'] == 'http://example.com/assets/client/boot.js'

    def test_does_not_use_client_boot_script_when_disabled(self, pyramid_request_):
        pyramid_request_.feature.flags['use_client_boot_script'] = False
        ctx = client.embed(pyramid_request_)
        assert ctx['client_boot_url'] is None

    def test_sets_content_type(self, pyramid_request_):
        client.embed(pyramid_request_)
        assert pyramid_request_.response.content_type == 'text/javascript'


@pytest.fixture
def pyramid_request_(pyramid_request):
    assets_client_env = Mock(spec_set=['urls'])
    assets_client_env.urls.return_value = []
    pyramid_request.registry['assets_client_env'] = assets_client_env
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('api.index', '/api')
    pyramid_config.add_route('assets_client', '/assets/client/{subpath}')
    pyramid_config.add_route('index', '/')
    pyramid_config.add_route('widget', '/app.html')


@pytest.fixture
def generate_jwt(patch):
    func = patch('h.views.client.generate_jwt')
    func.return_value = 'abc123'
    return func
