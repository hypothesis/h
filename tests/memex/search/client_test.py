# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from memex.search.client import get_client


class TestClient(object):
    pass


class TestGetClient(object):
    def test_initializes_client_with_host(self, settings, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[0] == 'search.svc'

    def test_initializes_client_with_index(self, settings, patched_client):
        get_client(settings)
        args, _ = patched_client.call_args
        assert args[1] == 'my-index'

    @pytest.mark.parametrize('key,value,settingkey', [
        ('max_retries', 7, 'es.client.max_retries'),
        ('retry_on_timeout', True, 'es.client.retry_on_timeout'),
        ('timeout', 15, 'es.client.timeout'),
        ('maxsize', 4, 'es.client_poolsize'),
    ])
    def test_client_configuration(self, settings, patched_client, key, value, settingkey):
        settings[settingkey] = value
        get_client(settings)

        _, kwargs = patched_client.call_args
        assert kwargs[key] == value

    @pytest.fixture
    def settings(self):
        return {
            'es.host': 'search.svc',
            'es.index': 'my-index',
        }

    @pytest.fixture
    def patched_client(self, patch):
        return patch('memex.search.client.Client')
