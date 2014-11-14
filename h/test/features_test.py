import unittest

import pytest

from h.features import Client
from h.features import SettingsStorage
from h.features import UnknownFeatureError


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


class TestSettingsStorage(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'foo.features.enabled_feature': 'on',
            'foo.features.disabled_feature': False,
        }

    def test_get_returns_boolean(self):
        s = SettingsStorage(self.settings, 'foo.features')

        assert s.get('enabled_feature') is True
        assert s.get('disabled_feature') is False

    def test_get_returns_none(self):
        s = SettingsStorage(self.settings, 'foo.features')

        assert s.get('unknown_feature') is None
