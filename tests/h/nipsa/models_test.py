# -*- coding: utf-8 -*-
import pytest
from sqlalchemy import exc

from h.nipsa import models


def test_init():
    nipsa_user = models.NipsaUser("test_id")
    assert nipsa_user.userid == "test_id"


def test_two_rows_with_same_id(db_session):
    db_session.add(models.NipsaUser("test_id"))
    with pytest.raises(exc.IntegrityError):
        db_session.add(models.NipsaUser("test_id"))
        db_session.flush()


def test_null_id(db_session):
    with pytest.raises(exc.IntegrityError):
        db_session.add(models.NipsaUser(None))
        db_session.flush()
