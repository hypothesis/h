# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import (datetime, timedelta)

import pytest

from h.auth import worker
from h.models import AuthTicket


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

    @pytest.fixture
    def celery(self, patch, db_session):
        cel = patch('h.auth.worker.celery', autospec=False)
        cel.request.db = db_session
        return cel
