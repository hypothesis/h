# -*- coding: utf-8 -*-
import pytest
from sqlalchemy import exc

from h import db
from h.api.nipsa import models


def test_init():
    nipsa_user = models.NipsaUser("test_id")
    assert nipsa_user.userid == "test_id"


def test_get_by_userid_with_matching_user():
    nipsa_user = models.NipsaUser("test_id")
    db.Session.add(nipsa_user)

    assert models.NipsaUser.get_by_userid("test_id") == nipsa_user


def test_get_by_userid_not_found():
    assert models.NipsaUser.get_by_userid("does not exist") is None


def test_all_with_no_rows():
    assert models.NipsaUser.all() == []


def test_all_with_one_row():
    nipsa_user = models.NipsaUser("test_id")
    db.Session.add(nipsa_user)

    assert models.NipsaUser.all() == [nipsa_user]


def test_all_with_multiple_rows():
    nipsa_user1 = models.NipsaUser("test_id1")
    db.Session.add(nipsa_user1)
    nipsa_user2 = models.NipsaUser("test_id2")
    db.Session.add(nipsa_user2)
    nipsa_user3 = models.NipsaUser("test_id3")
    db.Session.add(nipsa_user3)

    assert models.NipsaUser.all() == [nipsa_user1, nipsa_user2, nipsa_user3]


def test_two_rows_with_same_id():
    db.Session.add(models.NipsaUser("test_id"))
    with pytest.raises(exc.IntegrityError):
        db.Session.add(models.NipsaUser("test_id"))
        db.Session.flush()


def test_null_id():
    with pytest.raises(exc.IntegrityError):
        db.Session.add(models.NipsaUser(None))
        db.Session.flush()
