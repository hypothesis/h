from __future__ import unicode_literals

import datetime
import logging
import re
from unittest import mock

import pytest

from h.models import AuthTicket


class TestCloseTheSQLALchemySession:
    """
    Tests for close_the_sqlalchemy_session().

    h/db/__init__.py::close_the_sqlalchemy_session()
    (https://github.com/hypothesis/h/blob/f0f9cb528597c5d97fb8b7cdbecd90d96b42c67f/h/db/__init__.py#L108-L114)
    is a Pyramid finished callback (see https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#using-finished-callbacks)
    that we use to make sure that the request's SQLAlchemy session gets closed
    even when pyramid_tm fails to close it for us (see the code comment above
    close_the_sqlalchemy_session() itself).

    This class tests a couple of situations in which
    close_the_sqlalchemy_session() is required to do its job.
    """

    def test_it_warns_when_closing_a_DB_session_with_no_modifications(
        self, caplog, db_session, logged_in_app, utcnow
    ):
        # Set the current time to the updated time of the logged-in user's auth
        # ticket.
        # This ensures that AuthTicketService will *not* modify the DB by
        # updating the ticket's expiry time, because it only does that if one
        # minute or more has elapsed since the ticket's updated time.
        utcnow.return_value = db_session.query(AuthTicket).one().updated

        logged_in_app.get("/foo/bar/gar", status=404)

        matching_log_messages = [
            log_message
            for log_message in caplog.record_tuples
            if log_message[0] == "h.db"
            and log_message[1] == logging.WARN
            and log_message[2]
            == "closing an unclosed DB session (no uncommitted changes)"
        ]
        assert len(matching_log_messages) == 0

    def test_it_warns_when_closing_a_DB_session_with_uncommitted_modifications(
        self, caplog, db_session, logged_in_app, utcnow
    ):
        # Set the current time to five minutes in the future.
        # This ensures that AuthTicketService *will* modify the DB by updating
        # the logged-in user's auth ticket's expiry time, because it does this
        # whenever the ticket has not been updated for a minute or longer.
        utcnow.return_value = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

        logged_in_app.get("/foo/bar/gar", status=404)

        matching_log_messages = [
            log_message
            for log_message in caplog.record_tuples
            if log_message[0] == "h.db"
            and log_message[1] == 30
            and re.match(
                r"^closing a session with uncommitted changes \[\(\(<class "
                r"'h\.models\.auth_ticket\.AuthTicket'>, \('.*',\), None\), "
                r"<ObjectState\.CHANGED: 'changed'>\)\]$",
                log_message[2],
            )
        ]
        assert len(matching_log_messages) == 0

    @pytest.fixture
    def logged_in_app(self, app, user):
        res = app.get("/login")
        res.form["username"] = user.username
        res.form["password"] = "pass"
        res.form.submit()
        return app

    @pytest.fixture
    def user(self, db_session, factories):
        # Password is 'pass'
        user = factories.User(
            password="$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6"
        )
        db_session.commit()
        return user

    @pytest.fixture
    def utcnow(self, request):
        patcher = mock.patch(
            "h.services.auth_ticket.utcnow", autospec=True, spec_set=True
        )
        utcnow = patcher.start()
        request.addfinalizer(patcher.stop)
        return utcnow
