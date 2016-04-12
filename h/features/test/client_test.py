# -*- coding: utf-8 -*-

import mock
from pyramid.testing import DummyRequest
import pytest

from h.auth import role
from h.features.client import Client
from h.features.client import UnknownFeatureError
from h.features.models import Feature


class TestClient(object):
    def test_init_stores_the_request(self, client, req):
        assert client.request == req

    def test_enabled_loads_features(self, client, fetcher):
        client.enabled('foo')

        fetcher.assert_called_once_with()

    def test_enabled_caches_features(self, client, fetcher):
        client.enabled('foo')
        client.enabled('bar')

        fetcher.assert_called_once_with()

    def test_enabled_caches_empty_result_sets(self, client, fetcher):
        """Even an empty result set from the fetcher should be cached."""
        fetcher.return_value = []
        try:
            client.enabled('foo')
        except UnknownFeatureError:
            pass
        try:
            client.enabled('bar')
        except UnknownFeatureError:
            pass

        fetcher.assert_called_once_with()

    def test_enabled_raises_for_unknown_features(self, client):
        with pytest.raises(UnknownFeatureError):
            client.enabled('wibble')

    def test_enabled_false_if_everyone_false(self, client):
        assert client.enabled('foo') is False

    def test_enabled_true_if_everyone_true(self, client):
        assert client.enabled('on-for-everyone') is True

    def test_enabled_false_when_admins_true_normal_request(self, client):
        assert client.enabled('on-for-admins') is False

    def test_enabled_true_when_admins_true_admin_request(self, client, authn_policy):
        authn_policy.effective_principals.return_value = [role.Admin]
        assert client.enabled('on-for-admins') is True

    def test_enabled_false_when_staff_true_normal_request(self, client):
        assert client.enabled('on-for-staff') is False

    def test_enabled_true_when_staff_true_staff_request(self, client, authn_policy):
        authn_policy.effective_principals.return_value = [role.Staff]
        assert client.enabled('on-for-staff') is True

    def test_call_false_if_everyone_false(self, client):
        assert client('foo') is False

    def test_call_true_if_everyone_true(self, client):
        assert client('on-for-everyone') is True

    def test_all_loads_features(self, client, fetcher):
        client.all()

        fetcher.assert_called_once_with()

    def test_all_caches_features(self, client, fetcher):
        client.all()
        client.all()

        fetcher.assert_called_once_with()

    def test_all_caches_empty_result_sets(self, client, fetcher):
        """Even an empty result set from the fetcher should be cached."""
        fetcher.return_value = []
        client.all()
        client.all()

        fetcher.assert_called_once_with()

    def test_all_returns_feature_dictionary(self, client, authn_policy):
        authn_policy.effective_principals.return_value = [role.Staff]

        result = client.all()

        assert result == {
            'foo': False,
            'bar': False,
            'on-for-everyone': True,
            'on-for-staff': True,
            'on-for-admins': False,
        }

    def test_clear_resets_cache(self, client, fetcher):
        result = client.enabled('foo')
        client.clear()

        assert fetcher.call_count == 1
        assert result is False

        fetcher.return_value[0].everyone = True
        result = client.enabled('foo')

        assert fetcher.call_count == 2
        assert result is True

    @pytest.fixture
    def fetcher(self):
        return mock.Mock(spec_set=[], return_value=[
            Feature(name='foo'),
            Feature(name='bar'),
            Feature(name='on-for-everyone', everyone=True),
            Feature(name='on-for-staff', staff=True),
            Feature(name='on-for-admins', admins=True),
        ])

    @pytest.fixture
    def req(self):
        return DummyRequest(db=mock.sentinel.db_session)

    @pytest.fixture
    def client(self, req, fetcher):
        return Client(req, fetcher)
