import pytest
from sqlalchemy import exc

from h.api.nipsa import models


@pytest.mark.usefixtures("db_session")
def test_init():
    nipsa_user = models.NipsaUser("test_id")
    assert nipsa_user.userid == "test_id"


def test_get_by_id_with_matching_user(db_session):
    nipsa_user = models.NipsaUser("test_id")
    db_session.add(nipsa_user)

    assert models.NipsaUser.get_by_id("test_id") == nipsa_user


@pytest.mark.usefixtures("db_session")
def test_get_by_id_not_found():
    assert models.NipsaUser.get_by_id("does not exist") is None


@pytest.mark.usefixtures("db_session")
def test_all_with_no_rows():
    assert models.NipsaUser.all() == []


def test_all_with_one_row(db_session):
    nipsa_user = models.NipsaUser("test_id")
    db_session.add(nipsa_user)

    assert models.NipsaUser.all() == [nipsa_user]


def test_all_with_multiple_rows(db_session):
    nipsa_user1 = models.NipsaUser("test_id1")
    db_session.add(nipsa_user1)
    nipsa_user2 = models.NipsaUser("test_id2")
    db_session.add(nipsa_user2)
    nipsa_user3 = models.NipsaUser("test_id3")
    db_session.add(nipsa_user3)

    assert models.NipsaUser.all() == [nipsa_user1, nipsa_user2, nipsa_user3]


def test_two_rows_with_same_id(db_session):
    db_session.add(models.NipsaUser("test_id"))
    with pytest.raises(exc.IntegrityError):
        db_session.add(models.NipsaUser("test_id"))
        db_session.flush()


def test_null_id(db_session):
    with pytest.raises(exc.IntegrityError):
        db_session.add(models.NipsaUser(None))
        db_session.flush()
