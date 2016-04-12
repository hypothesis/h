# -*- coding: utf-8 -*-
import mock
from pyramid.testing import DummyRequest
import pytest

from h import db
from h import features
from h.auth import role


@pytest.fixture(scope='module', autouse=True)
def features_override(request):
    # Replace the primary FEATURES dictionary for the duration of testing...
    patcher = mock.patch.dict('h.features.FEATURES', {
        'notification': "A test flag for testing with."
    }, clear=True)
    patcher.start()
    request.addfinalizer(patcher.stop)


@pytest.fixture(scope='module', autouse=True)
def features_pending_removal_override(request):
    # And configure 'abouttoberemoved' as a feature pending removal...
    patcher = mock.patch.dict('h.features.FEATURES_PENDING_REMOVAL', {
        'abouttoberemoved': "A test flag that's about to be removed."
    }, clear=True)
    patcher.start()
    request.addfinalizer(patcher.stop)


class TestClient(object):
    def test_init_stores_the_request(self):
        request = DummyRequest()
        client = features.Client(request)
        assert client.request == request

    def test_init_initializes_an_empty_cache(self):
        client = features.Client(DummyRequest())
        assert client._cache == {}

    def test_load_loads_features(self, client):
        db.Session.add(features.Feature(name='notification'))
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
        db.Session.add(features.Feature(name='notification'))
        db.Session.add(features.Feature(name='new_homepage'))
        db.Session.flush()

        client.load()
        assert client._cache.keys() == ['notification']

    def test_load_skips_pending_removal_features(self, client):
        db.Session.add(features.Feature(name='notification'))
        db.Session.add(features.Feature(name='abouttoberemoved'))
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
        fetcher.return_value = [
            features.Feature(name='notification', everyone=False)]
        assert client.enabled('notification') is False

    def test_enabled_true_if_everyone_true(self, client, fetcher):
        fetcher.return_value = [
            features.Feature(name='notification', everyone=True)]
        assert client.enabled('notification') is True

    def test_enabled_false_when_admins_true_normal_request(self,
                                                           client,
                                                           fetcher):
        fetcher.return_value = [
            features.Feature(name='notification', admins=True)]
        assert client.enabled('notification') is False

    def test_enabled_true_when_admins_true_admin_request(self,
                                                         client,
                                                         fetcher,
                                                         authn_policy):
        authn_policy.effective_principals.return_value = [role.Admin]
        fetcher.return_value = [
            features.Feature(name='notification', admins=True)]
        assert client.enabled('notification') is True

    def test_enabled_false_when_staff_true_normal_request(self,
                                                          client,
                                                          fetcher):
        fetcher.return_value = [
            features.Feature(name='notification', staff=True)]

        assert client.enabled('notification') is False

    def test_enabled_true_when_staff_true_staff_request(self,
                                                        client,
                                                        fetcher,
                                                        authn_policy):
        authn_policy.effective_principals.return_value = [role.Staff]
        fetcher.return_value = [
            features.Feature(name='notification', staff=True)]

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
        return patch('h.features.Client._fetch_features')


def test_remove_old_flag_removes_old_flags():
    """
    The remove_old_flags function should remove unknown flags.

    New flags and flags pending removal should be left alone, but completely
    unknown flags should be removed.
    """
    new_feature = features.Feature(name='notification')
    pending_feature = features.Feature(name='abouttoberemoved')
    old_feature = features.Feature(name='somethingelse')
    db.Session.add_all([new_feature, pending_feature, old_feature])
    db.Session.flush()

    features.remove_old_flags()

    remaining = set([f.name for f in features.Feature.query.all()])
    assert remaining == {'abouttoberemoved', 'notification'}


@pytest.fixture
def feature_model(patch):
    model = patch('h.features.Feature')
    model.get_by_name.return_value.everyone = False
    model.get_by_name.return_value.admins = False
    return model
