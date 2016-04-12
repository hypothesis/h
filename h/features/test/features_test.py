# -*- coding: utf-8 -*-
import mock
from pyramid.testing import DummyRequest
import pytest

from h import db
from h import features
from h.features.models import Feature
from h.auth import role


@pytest.mark.usefixtures('features_override',
                         'features_pending_removal_override')
class TestClient(object):
    def test_init_stores_the_request(self):
        request = DummyRequest()
        client = features.Client(request)
        assert client.request == request

    def test_init_initializes_an_empty_cache(self):
        client = features.Client(DummyRequest())
        assert client._cache == {}

    def test_load_loads_features(self, client):
        db.Session.add(Feature(name='notification'))
        db.Session.flush()

        client.load()
        assert client._cache.keys() == ['notification']

    def test_load_includes_features_not_in_db(self, client):
        client.load()
        assert client._cache.keys() == ['notification']

    def test_load_skips_database_features_missing_from_dict(self, client):
        """
        Test that load does not load features that are still in the database
        but not in the FEATURES dict anymore
        """
        db.Session.add(Feature(name='notification'))
        db.Session.add(Feature(name='new_homepage'))
        db.Session.flush()

        client.load()
        assert client._cache.keys() == ['notification']

    def test_load_skips_pending_removal_features(self, client):
        db.Session.add(Feature(name='notification'))
        db.Session.add(Feature(name='abouttoberemoved'))
        db.Session.flush()

        client.load()
        assert client._cache.keys() == ['notification']

    def test_enabled_raises_for_undocumented_feature(self, client):
        with pytest.raises(features.UnknownFeatureError):
            client.enabled('wibble')

    def test_enabled_raises_for_feature_pending_removal(self, client):
        with pytest.raises(features.UnknownFeatureError):
            client.enabled('abouttoberemoved')

    def test_enabled_loads_cache_when_empty(self,
                                            client,
                                            client_load):

        def test_load(self):
            self._cache = {'notification': True}
        client_load.side_effect = test_load

        client._cache = {}
        client.enabled('notification')
        client_load.assert_called_with(client)

    def test_enabled_false_if_not_in_database(self, client):
        assert client.enabled('notification') is False

    def test_enabled_false_if_everyone_false(self, client, fetcher):
        fetcher.return_value = [Feature(name='notification', everyone=False)]
        assert client.enabled('notification') is False

    def test_enabled_true_if_everyone_true(self, client, fetcher):
        fetcher.return_value = [Feature(name='notification', everyone=True)]
        assert client.enabled('notification') is True

    def test_enabled_false_when_admins_true_normal_request(self,
                                                           client,
                                                           fetcher):
        fetcher.return_value = [Feature(name='notification', admins=True)]
        assert client.enabled('notification') is False

    def test_enabled_true_when_admins_true_admin_request(self,
                                                         client,
                                                         fetcher,
                                                         authn_policy):
        authn_policy.effective_principals.return_value = [role.Admin]
        fetcher.return_value = [Feature(name='notification', admins=True)]
        assert client.enabled('notification') is True

    def test_enabled_false_when_staff_true_normal_request(self,
                                                          client,
                                                          fetcher):
        fetcher.return_value = [Feature(name='notification', staff=True)]

        assert client.enabled('notification') is False

    def test_enabled_true_when_staff_true_staff_request(self,
                                                        client,
                                                        fetcher,
                                                        authn_policy):
        authn_policy.effective_principals.return_value = [role.Staff]
        fetcher.return_value = [Feature(name='notification', staff=True)]

        assert client.enabled('notification') is True

    def test_all_loads_cache_when_empty(self, client, client_load):
        client._cache = {}
        client.all()
        client_load.assert_called_with(client)

    def test_all_returns_cache(self, client):
        cache = mock.Mock()
        client._cache = cache
        assert client.all() == cache

    def test_clear(self, client):
        client._cache = mock.Mock()
        client.clear()
        assert client._cache == {}

    @pytest.fixture
    def client(self):
        return features.Client(DummyRequest(db=db.Session))

    @pytest.fixture
    def client_load(self, patch):
        return patch('h.features.Client.load')

    @pytest.fixture
    def fetcher(self, patch):
        return patch('h.features.models.Feature.all', autospec=None)

    @pytest.fixture
    def features_override(self, request):
        # Replace the primary FEATURES dictionary for the duration of testing...
        patcher = mock.patch.dict('h.features.models.FEATURES', {
            'notification': "A test flag for testing with."
        }, clear=True)
        patcher.start()
        request.addfinalizer(patcher.stop)

    @pytest.fixture
    def features_pending_removal_override(self, request):
        # And configure 'abouttoberemoved' as a feature pending removal...
        patcher = mock.patch.dict('h.features.models.FEATURES_PENDING_REMOVAL', {
            'abouttoberemoved': "A test flag that's about to be removed."
        }, clear=True)
        patcher.start()
        request.addfinalizer(patcher.stop)
