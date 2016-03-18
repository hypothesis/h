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
    def test_init_loads_features(self):
        db.Session.add(features.Feature(name='notification'))
        db.Session.flush()

        client = self.client()
        assert client._cache.keys() == ['notification']

    def test_init_skips_database_features_missing_from_dict(self):
        """
        Test that init does not load features that are still in the database
        but not in the FEATURES dict anymore
        """
        db.Session.add(features.Feature(name='new_homepage'))
        db.Session.flush()

        client = self.client()
        assert len(client._cache) == 0

    def test_init_skips_pending_removal_features(self):
        db.Session.add(features.Feature(name='abouttoberemoved'))
        db.Session.flush()

        client = self.client()
        assert len(client._cache) == 0

    def test_enabled_raises_for_undocumented_feature(self, client):
        with pytest.raises(features.UnknownFeatureError):
            client.enabled('wibble')

    def test_enabled_raises_for_feature_pending_removal(self, client):
        with pytest.raises(features.UnknownFeatureError):
            client.enabled('abouttoberemoved')

    def test_enabled_false_if_not_in_database(self, client):
        assert client.enabled('notification') == False

    def test_enabled_false_if_everyone_false(self, client):
        client._cache['notification'] = features.Feature(everyone=False)
        assert client.enabled('notification') == False

    def test_enabled_true_if_everyone_true(self, client):
        client._cache['notification'] = features.Feature(everyone=True)
        assert client.enabled('notification') == True

    def test_enabled_false_when_admins_true_normal_request(self, client):
        client._cache['notification'] = features.Feature(admins=True)
        assert client.enabled('notification') == False

    def test_enabled_true_when_admins_true_admin_request(self,
                                                         client,
                                                         authn_policy):
        client._cache['notification'] = features.Feature(admins=True)
        authn_policy.effective_principals.return_value = [role.Admin]
        assert client.enabled('notification') == True

    def test_enabled_false_when_staff_true_normal_request(self, client):
        client._cache['notification'] = features.Feature(staff=True)
        assert client.enabled('notification') == False

    def test_enabled_true_when_staff_true_staff_request(self,
                                                        client,
                                                        authn_policy):
        client._cache['notification'] = features.Feature(staff=True)
        authn_policy.effective_principals.return_value = [role.Staff]
        assert client.enabled('notification') == True

    def test_all_checks_enabled(self, client, enabled):
        client.all()
        enabled.assert_called_with('notification')

    def test_all_omits_features_pending_removal(self, client):
        assert client.all() == {'notification': False}

    @pytest.fixture
    def client(self):
        return features.Client(DummyRequest(db=db.Session))

    @pytest.fixture
    def enabled(self, request, client):
        patcher = mock.patch('h.features.Client.enabled')
        method = patcher.start()
        request.addfinalizer(patcher.stop)
        return method


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
def feature_model(request):
    patcher = mock.patch('h.features.Feature', autospec=True)
    request.addfinalizer(patcher.stop)
    model = patcher.start()
    model.get_by_name.return_value.everyone = False
    model.get_by_name.return_value.admins = False
    return model
