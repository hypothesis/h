# -*- coding: utf-8 -*-
import pytest

from h import db
from h.groups import models
from h.test import factories


def test_init():
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db.Session.add(group)
    db.Session.flush()

    assert group.id
    assert group.name == name
    assert group.created
    assert group.updated
    assert group.creator == user
    assert group.creator_id == user.id
    assert group.members == [user]


def test_with_short_name():
    """Should raise ValueError if name shorter than 4 characters."""
    with pytest.raises(ValueError):
        models.Group(name="abc", creator=factories.User())


def test_with_long_name():
    """Should raise ValueError if name longer than 25 characters."""
    with pytest.raises(ValueError):
        models.Group(name="abcdefghijklmnopqrstuvwxyz",
                     creator=factories.User())


def test_slug():
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db.Session.add(group)
    db.Session.flush()

    assert group.slug == "my-hypothesis-group"


def test_repr():
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db.Session.add(group)
    db.Session.flush()

    assert repr(group) == "<Group: my-hypothesis-group>"


def test_get_by_id_when_id_does_exist():
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db.Session.add(group)
    db.Session.flush()

    assert models.Group.get_by_id(group.id) == group


def test_get_by_id_when_id_does_not_exist():
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, creator=user)
    db.Session.add(group)
    db.Session.flush()

    assert models.Group.get_by_id(23) is None
