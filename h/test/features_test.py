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
    feature_model.get_by_name.return_value.everyone = False
    request = DummyRequest()

    result = features.flag_enabled(request, 'notification')

    assert not result


def test_flag_enabled_true_if_everyone_true(feature_model):
    feature_model.get_by_name.return_value.everyone = True
    request = DummyRequest()

    result = features.flag_enabled(request, 'notification')

    assert result


@pytest.fixture
def feature_model(request):
    patcher = mock.patch('h.features.Feature', autospec=True)
    request.addfinalizer(patcher.stop)
    model = patcher.start()
    return model
