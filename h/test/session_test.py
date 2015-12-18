import unittest

import pytest
from mock import Mock
from mock import patch

from h.session import model


class FakeGroup():
    def __init__(self, pubid, name):
        self.pubid = pubid
        self.name = name
        self.slug = pubid


@patch('h.models.User')
def test_sorts_groups(User):
    fake_user = Mock()
    fake_user.groups = [
        FakeGroup('c', 'Group A'),
        FakeGroup('b', 'Group B'),
        FakeGroup('a', 'Group B'),
    ]
    request = Mock(authenticated_user=fake_user)
    session_model = model(request)

    ids = [group['id'] for group in session_model['groups']]
    assert ids == ['__world__', 'c', 'a', 'b']


@patch('h.session.features')
def test_includes_features(features, fake_user):
    feature_dict = {
        'feature_one': True,
        'feature_two': False,
    }
    features.all = Mock(return_value=feature_dict)
    request = Mock(authenticated_user=fake_user)
    assert model(request)['features'] == feature_dict


@pytest.fixture
def fake_user():
    fake_user = Mock()
    fake_user.groups = []
    return fake_user
