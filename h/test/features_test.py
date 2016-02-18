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


def test_flag_enabled_raises_for_undocumented_feature():
    request = DummyRequest()

    with pytest.raises(features.UnknownFeatureError):
        features.flag_enabled(request, 'wibble')


def test_flag_enabled_raises_for_feature_pending_removal():
    request = DummyRequest()

    with pytest.raises(features.UnknownFeatureError):
        features.flag_enabled(request, 'abouttoberemoved')


def test_flag_enabled_looks_up_feature_by_name(feature_model):
    request = DummyRequest()

    features.flag_enabled(request, 'notification')

    feature_model.get_by_name.assert_called_with('notification')


def test_flag_enabled_false_if_not_in_database(feature_model):
    feature_model.get_by_name.return_value = None
    request = DummyRequest()

    result = features.flag_enabled(request, 'notification')

    assert not result


def test_flag_enabled_false_if_everyone_false(feature_model):
    request = DummyRequest()

    result = features.flag_enabled(request, 'notification')

    assert not result


def test_flag_enabled_true_if_everyone_true(feature_model):
    feature_model.get_by_name.return_value.everyone = True
    request = DummyRequest()

    result = features.flag_enabled(request, 'notification')

    assert result


def test_flag_enabled_false_when_admins_true_normal_request(feature_model):
    feature_model.get_by_name.return_value.admins = True
    request = DummyRequest()

    result = features.flag_enabled(request, 'notification')

    assert not result


def test_flag_enabled_true_when_admins_true_admin_request(authn_policy,
                                                          feature_model):
    authn_policy.effective_principals.return_value = [role.Admin]
    feature_model.get_by_name.return_value.admins = True
    request = DummyRequest()

    result = features.flag_enabled(request, 'notification')

    assert result


def test_flag_enabled_false_when_staff_true_normal_request(feature_model):
    """It should return False for staff features if user is not staff.

    If a feature is enabled for staff, and the user is not a staff member,
    flag_enabled() should return False.

    """
    # The feature is enabled for staff members.
    feature_model.get_by_name.return_value.staff = True

    request = DummyRequest()

    assert features.flag_enabled(request, 'notification') is False


def test_flag_enabled_true_when_staff_true_staff_request(authn_policy,
                                                         feature_model):
    # The authorized user is a staff member.
    authn_policy.effective_principals.return_value = [role.Staff]

    # The feature is enabled for staff.
    feature_model.get_by_name.return_value.staff = True

    request = DummyRequest()

    assert features.flag_enabled(request, 'notification') is True


@pytest.mark.usefixtures('feature_model')
def test_all_omits_features_pending_removal():
    request = DummyRequest()

    assert features.all(request) == {'notification': False}


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
