# -*- coding: utf-8 -*-

import json
import mock
import pytest

from h.client import render_app_html
from h import __version__


class TestAppHtml(object):

    def test_it_includes_client_config(self, jinja_env):
        assets_env = mock.Mock(spec_set=['urls'])
        template = mock.Mock(spec_set=['render'])
        jinja_env.get_template.return_value = template

        render_app_html(assets_env=assets_env,
                        service_url='https://hypothes.is/',
                        api_url='https://hypothes.is/api',
                        sentry_public_dsn='test-sentry-dsn',
                        ga_client_tracking_id='UA-4567',
                        websocket_url='wss://hypothes.is/')

        expected_config = {
                'apiUrl': 'https://hypothes.is/api',
                'websocketUrl': 'wss://hypothes.is/',
                'serviceUrl': 'https://hypothes.is/',
                'release': __version__,
                'raven': {
                    'dsn': 'test-sentry-dsn',
                    'release': __version__
                },
                'googleAnalytics': 'UA-4567'
                }
        ((context,), kwargs) = template.render.call_args
        actual_config = json.loads(context['app_config'])
        assert actual_config == expected_config

    @pytest.fixture
    def jinja_env(self, patch):
        jinja_env = patch('h.client.jinja_env')
        return jinja_env
