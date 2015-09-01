# -*- coding: utf-8 -*-
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


def test_hashid_calls_encode(db_session):
    hashids = mock.Mock()
    group = models.Group('my-group', factories.User())

    group.hashid(hashids)

    hashids.encode.assert_called_once_with('h.groups', group.id)


def test_hashid_returns_encoded_hashid(db_session):
    hashids = mock.Mock()
    hashid = models.Group('my-group', factories.User()).hashid(hashids)

    assert hashid == hashids.encode.return_value


@mock.patch('h.api.groups.models.Group.get_by_id')
def test_get_by_hashid_calls_decode(get_by_id):
    hashids = mock.Mock()

    models.Group.get_by_hashid(hashids, 'test-hashid')

    hashids.decode.assert_called_once_with('h.groups', 'test-hashid')


@mock.patch('h.api.groups.models.Group.get_by_id')
def test_get_by_hashid_calls_get_by_id(get_by_id):
    hashids = mock.Mock()

    models.Group.get_by_hashid(hashids, 'test-hashid')

    get_by_id.assert_called_once_with(hashids.decode.return_value)


@mock.patch('h.api.groups.models.Group.get_by_id')
def test_get_by_hashid_calls_get_by_id(get_by_id):
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
    hashids = mock.Mock()

    assert group.as_dict(hashids) == {
        'name': 'My Hypothesis Group',
        'id': 'group:{}'.format(group.hashid(hashids))
    }
