# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.nipsa import NipsaService
from h.services.nipsa import nipsa_factory


@pytest.mark.usefixtures('users', 'reindex_user_annotations')
class TestNipsaService(object):
    def test_flagged_userids_returns_set_of_userids(self, db_session):
        svc = NipsaService(db_session)

        assert svc.flagged_userids == set(['acct:renata@example.com',
                                           'acct:cecilia@example.com'])

    def test_is_flagged_returns_true_for_flagged_users(self, db_session, users):
        svc = NipsaService(db_session)

        assert svc.is_flagged('acct:renata@example.com')
        assert svc.is_flagged('acct:cecilia@example.com')

    def test_is_flagged_returns_false_for_unflagged_users(self, db_session):
        svc = NipsaService(db_session)

        assert not svc.is_flagged('acct:dominic@example.com')
        assert not svc.is_flagged('acct:romeo@example.com')

    def test_flag_sets_nipsa_true(self, db_session, users):
        svc = NipsaService(db_session)

        svc.flag(users['dominic'])

        assert users['dominic'].nipsa is True

    def test_flag_triggers_reindex_job(self, db_session, users, reindex_user_annotations):
        svc = NipsaService(db_session)

        svc.flag(users['dominic'])

        reindex_user_annotations.delay.assert_called_once_with('acct:dominic@example.com')

    def test_unflag_sets_nipsa_false(self, db_session, users):
        svc = NipsaService(db_session)

        svc.unflag(users['renata'])

        assert users['renata'].nipsa is False

    def test_unflag_triggers_reindex_job(self, db_session, users, reindex_user_annotations):
        svc = NipsaService(db_session)

        svc.unflag(users['renata'])

        reindex_user_annotations.delay.assert_called_once_with('acct:renata@example.com')


def test_nipsa_factory(pyramid_request):
    svc = nipsa_factory(None, pyramid_request)

    assert isinstance(svc, NipsaService)
    assert svc.session == pyramid_request.db


@pytest.fixture
def reindex_user_annotations(patch):
    return patch('h.services.nipsa.reindex_user_annotations')


@pytest.fixture
def users(db_session, factories):
    users = {
        'renata': factories.User(username='renata', nipsa=True),
        'cecilia': factories.User(username='cecilia', nipsa=True),
        'dominic': factories.User(username='dominic', nipsa=False),
    }
    db_session.flush()
    return users
