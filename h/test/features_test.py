import unittest

from mock import patch
from pyramid.testing import DummyRequest
import pytest

from h.features import Client
from h.features import UnknownFeatureError
from h.features import get_client


class TestClient(unittest.TestCase):
    def setUp(self):
        self.storage = {
            'enabled_feature': True,
            'disabled_feature': False
        }

    def test_call_truthiness(self):
        c = Client(self.storage)

        assert c('enabled_feature')
        assert not c('disabled_feature')

    def test_call_raises(self):
        c = Client(self.storage)

        with pytest.raises(UnknownFeatureError):
            c('unknown_feature')


@patch('h.features.Client')
def test_get_client(client_mock, config):
    config.registry.settings.update({
        'h.feature.enabled_feature': 'on',
        'h.feature.disabled_feature': False,
        'unrelated_feature': 123,
    })

    request = DummyRequest(registry=config.registry)
    get_client(request)

    client_mock.assert_called_with({
        'enabled_feature': True,
        'disabled_feature': False
    })
