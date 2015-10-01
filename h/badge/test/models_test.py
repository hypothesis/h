# -*- coding: utf-8 -*-
import pytest
import mock

from h.badge import models


def test_cannot_add_same_uri_twice(db_session):
    db_session.add(models.BadgeBlocklist(uri="test_uri"))
    db_session.flush()

    with pytest.raises(ValueError):
        models.BadgeBlocklist(uri="test_uri")


def test_get_by_uri_returns_model(db_session):
    model = models.BadgeBlocklist(uri="test_uri")
    db_session.add(model)
    db_session.flush()

    assert models.BadgeBlocklist.get_by_uri("test_uri") == model


def test_get_by_uri_returns_None_if_no_match(db_session):
    model = models.BadgeBlocklist(uri="test_uri")
    db_session.add(model)
    db_session.flush()

    assert models.BadgeBlocklist.get_by_uri("another_uri") is None


def test_all(db_session):
    uris = [
        models.BadgeBlocklist(uri="first"),
        models.BadgeBlocklist(uri="second"),
        models.BadgeBlocklist(uri="third")
    ]
    for uri in uris:
        db_session.add(uri)
    db_session.flush()

    assert models.BadgeBlocklist.all() == uris


@mock.patch('h.badge.models.BadgeBlocklist.all')
def test_is_blocked(all):
    all.return_value = ["http://example.com", "http://example.com/bar"]

    assert models.BadgeBlocklist.is_blocked("http://example.com")
    assert models.BadgeBlocklist.is_blocked("http://example.com/bar")
    assert not models.BadgeBlocklist.is_blocked("http://example.com/foo")


@mock.patch('h.badge.models.BadgeBlocklist.all')
def test_is_blocked(all):
    all.return_value = ["*//example.com*"]

    assert models.BadgeBlocklist.is_blocked("http://example.com")
    assert models.BadgeBlocklist.is_blocked("http://example.com/bar")
    assert models.BadgeBlocklist.is_blocked("http://example.com/foo")
