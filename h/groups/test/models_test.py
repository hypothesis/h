# -*- coding: utf-8 -*-
from h.groups import models
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
