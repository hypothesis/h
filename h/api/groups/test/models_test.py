import mock

from h.api.groups import models
from h.test import factories


def test_init(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert group.id
    assert group.name == name
    assert group.created
    assert group.updated
    assert group.creator == user
    assert group.creator_id == user.id
    assert group.members == [user]


def test_slug(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert group.slug == "my-hypothesis-group"


@mock.patch('h.api.groups.models.hashids')
def test_hashid_calls_encode(hashids, db_session):
    request = mock.Mock()
    group = models.Group('my-group', factories.User())

    group.hashid(request)

    hashids.encode.assert_called_once_with(request, 'h.groups', group.id)


@mock.patch('h.api.groups.models.hashids')
def test_hashid_returns_encoded_hashid(hashids, db_session):
    hashid = models.Group('my-group', factories.User()).hashid(mock.Mock())

    assert hashid == hashids.encode.return_value


@mock.patch('h.api.groups.models.Group.get_by_id')
@mock.patch('h.api.groups.models.hashids')
def test_get_by_hashid_calls_decode(hashids, get_by_id):
    request = mock.Mock()

    models.Group.get_by_hashid(request, 'test-hashid')

    hashids.decode.assert_called_once_with(request, 'h.groups', 'test-hashid')


@mock.patch('h.api.groups.models.Group.get_by_id')
@mock.patch('h.api.groups.models.hashids')
def test_get_by_hashid_calls_get_by_id(hashids, get_by_id):
    request = mock.Mock()

    models.Group.get_by_hashid(request, 'test-hashid')

    get_by_id.assert_called_once_with(hashids.decode.return_value)


@mock.patch('h.api.groups.models.Group.get_by_id')
@mock.patch('h.api.groups.models.hashids')
def test_get_by_hashid_calls_get_by_id(hashids, get_by_id):
    user = models.Group.get_by_hashid(mock.Mock(), 'test-hashid')

    assert user == get_by_id.return_value


def test_repr(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert repr(group) == "<Group: my-hypothesis-group>"


def test_get_by_id_when_id_does_exist(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert models.Group.get_by_id(group.id) == group


def test_get_by_id_when_id_does_not_exist(db_session):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()

    assert models.Group.get_by_id(23) is None


def test_as_dict(db_session):
    name = "My Hypothesis Group"
    user = factories.User()
    group = models.Group(name=name, creator=user)
    db_session.add(group)
    db_session.flush()
    request = mock.MagicMock()

    assert group.as_dict(request) == {
        'name': 'My Hypothesis Group',
        'hashid': group.hashid(request)
    }
