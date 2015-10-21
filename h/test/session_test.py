import unittest

from mock import Mock
from mock import patch

from h.session import model


class FakeGroup():
    def __init__(self, hashid, name):
        self.hashid = hashid
        self.name = name
        self.slug = hashid


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
