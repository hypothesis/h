# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest
from pyramid.testing import DummyRequest

from h.nipsa.models import NipsaUser
from h.nipsa.services import NipsaService
from h.nipsa.services import nipsa_factory


@pytest.mark.usefixtures('nipsa_users', 'worker')
class TestNipsaService(object):
    def test_flagged_userids_returns_list_of_userids(self, db_session):
        svc = NipsaService(db_session)

        assert set(svc.flagged_userids) == set(['acct:renata@example.com',
                                                'acct:cecilia@example.com',
                                                'acct:dominic@example.com'])

    def test_is_flagged_returns_true_for_flagged_userids(self, db_session):
        svc = NipsaService(db_session)

        assert svc.is_flagged('acct:renata@example.com')
        assert svc.is_flagged('acct:cecilia@example.com')

    def test_is_flagged_returns_false_for_unflagged_userids(self, db_session):
        svc = NipsaService(db_session)

        assert not svc.is_flagged('acct:dochia@example.com')
        assert not svc.is_flagged('acct:romeo@example.com')

    def test_flag_adds_record_to_database(self, db_session):
        svc = NipsaService(db_session)

        svc.flag('acct:ethan@example.com')

        user_query = db_session.query(NipsaUser).filter_by(userid='acct:ethan@example.com')
        assert user_query.one_or_none() is not None

    def test_flag_is_idempotent(self, db_session):
        svc = NipsaService(db_session)

        svc.flag('acct:juno@example.com')
        svc.flag('acct:juno@example.com')

        user_query = db_session.query(NipsaUser).filter_by(userid='acct:juno@example.com')
        assert user_query.one_or_none() is not None

    def test_unflag_removes_record_from_database(self, db_session):
        svc = NipsaService(db_session)

        svc.unflag('acct:renata@example.com')

        user_query = db_session.query(NipsaUser).filter_by(userid='acct:renata@example.com')
        assert user_query.one_or_none() is None

    def test_unflag_is_idempotent(self, db_session):
        svc = NipsaService(db_session)

        svc.unflag('acct:dominic@example.com')
        svc.unflag('acct:dominic@example.com')

        user_query = db_session.query(NipsaUser).filter_by(userid='acct:dominic@example.com')
        assert user_query.one_or_none() is None


def test_nipsa_factory():
    request = DummyRequest(db=mock.sentinel.db_session)

    svc = nipsa_factory(None, request)

    assert isinstance(svc, NipsaService)
    assert svc.session == mock.sentinel.db_session


@pytest.fixture
def nipsa_users(db_session):
    flagged_userids = ['acct:renata@example.com',
                       'acct:cecilia@example.com',
                       'acct:dominic@example.com']
    instances = []

    for userid in flagged_userids:
        instances.append(NipsaUser(userid=userid))

    db_session.add_all(instances)
    db_session.flush()


@pytest.fixture
def worker(patch):
    return patch('h.nipsa.services.worker')
