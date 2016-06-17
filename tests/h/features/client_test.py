# -*- coding: utf-8 -*-

import mock
import pytest

from h.auth import role
from h.models import Feature, FeatureCohort, User
from h.features.client import Client
from h.features.client import UnknownFeatureError


class TestClient(object):
    def test_init_stores_the_request(self, client, pyramid_request):
        assert client.request == pyramid_request

    def test_enabled_loads_features(self, client, fetcher, pyramid_request):
        client.enabled('foo')

        fetcher.assert_called_once_with(pyramid_request.db)

    def test_enabled_caches_features(self, client, fetcher, pyramid_request):
        client.enabled('foo')
        client.enabled('bar')

        fetcher.assert_called_once_with(pyramid_request.db)

    def test_enabled_caches_empty_result_sets(self, client, fetcher, pyramid_request):
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

        fetcher.assert_called_once_with(pyramid_request.db)

    def test_enabled_raises_for_unknown_features(self, client):
        with pytest.raises(UnknownFeatureError):
            client.enabled('wibble')

    def test_enabled_false_if_everyone_false(self, client):
        assert client.enabled('foo') is False

    def test_enabled_true_if_everyone_true(self, client):
        assert client.enabled('on-for-everyone') is True

    def test_enabled_false_when_admins_true_normal_request(self, client):
        assert client.enabled('on-for-admins') is False

    def test_enabled_true_when_admins_true_admin_request(self, client, pyramid_config):
        pyramid_config.testing_securitypolicy('acct:foo@example.com',
                                              groupids=[role.Admin])
        assert client.enabled('on-for-admins') is True

    def test_enabled_false_when_staff_true_normal_request(self, client):
        assert client.enabled('on-for-staff') is False

    def test_enabled_true_when_staff_true_staff_request(self, client, pyramid_config):
        pyramid_config.testing_securitypolicy('acct:foo@example.com',
                                              groupids=[role.Staff])
        assert client.enabled('on-for-staff') is True

    def test_call_false_if_everyone_false(self, client):
        assert client('foo') is False

    def test_call_true_if_everyone_true(self, client):
        assert client('on-for-everyone') is True

    def test_call_false_if_cohort_disabled(self, client):
        assert client('on-for-cohort') is False

    def test_call_true_if_cohort_enabled(self, patch, client, user, cohort):
        user.cohorts = [cohort]
        assert client('on-for-cohort') is True

    def test_call_false_if_unauthenticated_user(self, patch, client, pyramid_request):
        pyramid_request.authenticated_user = None
        assert client('on-for-cohort') is False

    def test_all_loads_features(self, client, fetcher, pyramid_request):
        client.all()

        fetcher.assert_called_once_with(pyramid_request.db)

    def test_all_caches_features(self, client, fetcher, pyramid_request):
        client.all()
        client.all()

        fetcher.assert_called_once_with(pyramid_request.db)

    def test_all_caches_empty_result_sets(self, client, fetcher, pyramid_request):
        """Even an empty result set from the fetcher should be cached."""
        fetcher.return_value = []
        client.all()
        client.all()

        fetcher.assert_called_once_with(pyramid_request.db)

    def test_all_returns_feature_dictionary(self, client, pyramid_config):
        pyramid_config.testing_securitypolicy('acct:foo@example.com',
                                              groupids=[role.Staff])

        result = client.all()

        assert result == {
            'foo': False,
            'bar': False,
            'on-for-everyone': True,
            'on-for-staff': True,
            'on-for-admins': False,
            'on-for-cohort': False,
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
    def fetcher(self, cohort):
        return mock.Mock(spec_set=[], return_value=[
            Feature(name='foo'),
            Feature(name='bar'),
            Feature(name='on-for-everyone', everyone=True),
            Feature(name='on-for-staff', staff=True),
            Feature(name='on-for-admins', admins=True),
            Feature(name='on-for-cohort', cohorts=[cohort])
        ])

    @pytest.fixture
    def user(self):
        return User(username='foo', email='foo@example.com', password='bar')

    @pytest.fixture
    def cohort(self):
        return FeatureCohort(name='cohort')

    @pytest.fixture
    def client(self, pyramid_request, fetcher):
        return Client(pyramid_request, fetcher)

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.authenticated_user = user
        return pyramid_request
