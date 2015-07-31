import mock
from pyramid.testing import DummyRequest
import pytest

from h import features


def test_flag_enabled_raises_for_undocumented_feature():
    request = DummyRequest()

    with pytest.raises(features.UnknownFeatureError):
        features.flag_enabled(request, 'wibble')


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
    authn_policy.effective_principals.return_value = ['group:admin']
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
    authn_policy.effective_principals.return_value = ['group:staff']

    # The feature is enabled for staff.
    feature_model.get_by_name.return_value.staff = True

    request = DummyRequest()

    assert features.flag_enabled(request, 'notification') is True


@pytest.fixture
def feature_model(request):
    patcher = mock.patch('h.features.Feature', autospec=True)
    request.addfinalizer(patcher.stop)
    model = patcher.start()
    model.get_by_name.return_value.everyone = False
    model.get_by_name.return_value.admins = False
    return model
