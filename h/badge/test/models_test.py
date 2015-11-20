# -*- coding: utf-8 -*-
import pytest

from h import db
from h.badge import models


def test_cannot_add_same_uri_twice():
    db.Session.add(models.Blocklist(uri="test_uri"))
    db.Session.flush()

    with pytest.raises(ValueError):
        models.Blocklist(uri="test_uri")


def test_get_by_uri_returns_model():
    model = models.Blocklist(uri="test_uri")
    db.Session.add(model)
    db.Session.flush()

    assert models.Blocklist.get_by_uri("test_uri") == model


def test_get_by_uri_returns_None_if_no_match():
    model = models.Blocklist(uri="test_uri")
    db.Session.add(model)
    db.Session.flush()

    assert models.Blocklist.get_by_uri("another_uri") is None


def test_all():
    uris = [
        models.Blocklist(uri="first"),
        models.Blocklist(uri="second"),
        models.Blocklist(uri="third")
    ]
    for uri in uris:
        db.Session.add(uri)
    db.Session.flush()

    assert models.Blocklist.all() == uris


def test_is_blocked():
    db.Session.add(models.Blocklist(uri=u"http://example.com"))
    db.Session.add(models.Blocklist(uri=u"http://example.com/bar"))
    db.Session.flush()

    assert models.Blocklist.is_blocked(u"http://example.com")
    assert models.Blocklist.is_blocked(u"http://example.com/bar")
    assert not models.Blocklist.is_blocked(u"http://example.com/foo")


def test_is_blocked_with_wildcards():
    db.Session.add(models.Blocklist(uri="%//example.com%"))
    db.Session.flush()

    assert models.Blocklist.is_blocked("http://example.com/")
    assert models.Blocklist.is_blocked("http://example.com/bar")
    assert models.Blocklist.is_blocked("http://example.com/foo")
