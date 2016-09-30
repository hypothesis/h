# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import (datetime, timedelta)

import pytest

from h.auth import worker
from h.models import (AuthTicket, Token)


@pytest.mark.usefixtures('celery')
class TestDeleteExpiredAuthTickets(object):
    def test_it_removes_expired_tickets(self, db_session, factories):
        tickets = [
            factories.AuthTicket(expires=datetime(2014, 5, 6, 7, 8, 9)),
            factories.AuthTicket(expires=(datetime.utcnow() - timedelta(seconds=1))),
        ]
        db_session.add_all(tickets)

        assert db_session.query(AuthTicket).count() == 2
        worker.delete_expired_auth_tickets()
        assert db_session.query(AuthTicket).count() == 0

    def test_it_leaves_valid_tickets(self, db_session, factories):
        tickets = [
            factories.AuthTicket(expires=datetime(2014, 5, 6, 7, 8, 9)),
            factories.AuthTicket(expires=(datetime.utcnow() + timedelta(hours=1))),
        ]
        db_session.add_all(tickets)

        assert db_session.query(AuthTicket).count() == 2
        worker.delete_expired_auth_tickets()
        assert db_session.query(AuthTicket).count() == 1


@pytest.mark.usefixtures('celery')
class TestDeleteExpiredTokens(object):
    def test_it_removes_expired_tokens(self, db_session, factories):
        factories.Token(expires=datetime(2014, 5, 6, 7, 8, 9))
        factories.Token(expires=(datetime.utcnow() - timedelta(seconds=1)))

        assert db_session.query(Token).count() == 2
        worker.delete_expired_tokens()
        assert db_session.query(Token).count() == 0

    def test_it_leaves_valid_tickets(self, db_session, factories):
        factories.Token(expires=datetime(2014, 5, 6, 7, 8, 9))
        factories.Token(expires=(datetime.utcnow() + timedelta(hours=1)))

        assert db_session.query(Token).count() == 2
        worker.delete_expired_tokens()
        assert db_session.query(Token).count() == 1

    def test_it_leaves_tickets_without_an_expiration_date(self, db_session, factories):
        factories.Token(expires=None)
        factories.Token(expires=None)

        assert db_session.query(Token).count() == 2
        worker.delete_expired_tokens()
        assert db_session.query(Token).count() == 2


@pytest.fixture
def celery(patch, db_session):
    cel = patch('h.auth.worker.celery', autospec=False)
    cel.request.db = db_session
    return cel
