from datetime import datetime, timedelta

import pytest

from h.models import AuthTicket, AuthzCode, Token
from h.tasks.cleanup import (
    purge_deleted_annotations,
    purge_deleted_users,
    purge_expired_auth_tickets,
    purge_expired_authz_codes,
    purge_expired_tokens,
    purge_removed_features,
    report_num_deleted_annotations,
)


@pytest.mark.usefixtures("celery")
class TestPurgeDeletedAnnotations:
    def test_purge(self, annotation_delete_service):
        purge_deleted_annotations()

        annotation_delete_service.bulk_delete.assert_called_once()


@pytest.mark.usefixtures("celery")
class TestReportNumDeletedAnnotations:
    def test_report_num_deleted_annotations(self, factories, newrelic):
        # Annotations marked as deleted, these should be counted.
        factories.Annotation.create_batch(2, deleted=True)
        # An annotation not marked as deleted, this should not be counted.
        factories.Annotation.create()

        report_num_deleted_annotations()

        newrelic.agent.record_custom_metric.assert_called_once_with(
            "Custom/Annotations/MarkedAsDeleted", 2
        )


@pytest.mark.usefixtures("celery")
class TestPurgeExpiredAuthTickets:
    def test_it_removes_expired_tickets(self, db_session, factories):
        tickets = [
            factories.AuthTicket(expires=datetime(2014, 5, 6, 7, 8, 9)),
            factories.AuthTicket(expires=(datetime.utcnow() - timedelta(seconds=1))),
        ]
        db_session.add_all(tickets)

        assert db_session.query(AuthTicket).count() == 2
        purge_expired_auth_tickets()
        assert not db_session.query(AuthTicket).count()

    def test_it_leaves_valid_tickets(self, db_session, factories):
        tickets = [
            factories.AuthTicket(expires=datetime(2014, 5, 6, 7, 8, 9)),
            factories.AuthTicket(expires=(datetime.utcnow() + timedelta(hours=1))),
        ]
        db_session.add_all(tickets)

        assert db_session.query(AuthTicket).count() == 2
        purge_expired_auth_tickets()
        assert db_session.query(AuthTicket).count() == 1


@pytest.mark.usefixtures("celery")
class TestPurgeExpiredAuthzCodes:
    def test_it_removes_expired_authz_codes(self, db_session, factories):
        authz_codes = [
            factories.AuthzCode(expires=datetime(2014, 5, 6, 7, 8, 9)),
            factories.AuthzCode(expires=(datetime.utcnow() - timedelta(seconds=1))),
        ]
        db_session.add_all(authz_codes)

        assert db_session.query(AuthzCode).count() == 2
        purge_expired_authz_codes()
        assert not db_session.query(AuthzCode).count()

    def test_it_leaves_valid_authz_codes(self, db_session, factories):
        authz_codes = [
            factories.AuthzCode(expires=datetime(2014, 5, 6, 7, 8, 9)),
            factories.AuthzCode(expires=(datetime.utcnow() + timedelta(hours=1))),
        ]
        db_session.add_all(authz_codes)

        assert db_session.query(AuthzCode).count() == 2
        purge_expired_authz_codes()
        assert db_session.query(AuthzCode).count() == 1


@pytest.mark.usefixtures("celery")
class TestPurgeExpiredTokens:
    def test_it_removes_expired_tokens(self, db_session, factories):
        factories.DeveloperToken(
            expires=datetime(2014, 5, 6, 7, 8, 9),
            refresh_token_expires=datetime(2014, 5, 13, 7, 8, 9),
        )
        factories.DeveloperToken(
            expires=(datetime.utcnow() - timedelta(hours=2)),
            refresh_token_expires=(datetime.utcnow() - timedelta(seconds=1)),
        )

        assert db_session.query(Token).count() == 2
        purge_expired_tokens()
        assert not db_session.query(Token).count()

    def test_it_leaves_valid_tickets(self, db_session, factories):
        factories.DeveloperToken(
            expires=datetime(2014, 5, 6, 7, 8, 9),
            refresh_token_expires=datetime(2014, 5, 13, 7, 8, 9),
        )
        factories.DeveloperToken(
            expires=(datetime.utcnow() + timedelta(hours=1)),
            refresh_token_expires=datetime.utcnow() + timedelta(days=7),
        )
        factories.DeveloperToken(
            expires=(datetime.utcnow() - timedelta(hours=1)),
            refresh_token_expires=datetime.utcnow() + timedelta(days=7),
        )
        factories.DeveloperToken(
            expires=(datetime.utcnow() + timedelta(hours=1)),
            refresh_token_expires=datetime.utcnow() - timedelta(days=7),
        )

        assert db_session.query(Token).count() == 4
        purge_expired_tokens()
        assert db_session.query(Token).count() == 3

    def test_it_leaves_tickets_without_an_expiration_date(self, db_session, factories):
        factories.DeveloperToken(expires=None)
        factories.DeveloperToken(expires=None)

        assert db_session.query(Token).count() == 2
        purge_expired_tokens()
        assert db_session.query(Token).count() == 2


@pytest.mark.usefixtures("celery")
class TestPurgeRemovedFeatures:
    def test_calls_remove_old_flags(self, db_session, patch):
        Feature = patch("h.tasks.cleanup.models.Feature")

        purge_removed_features()

        Feature.remove_old_flags.assert_called_once_with(db_session)


@pytest.mark.usefixtures("celery")
class TestPurgeDeletedUsers:
    def test_it(self, user_delete_service):
        purge_deleted_users()

        user_delete_service.purge_deleted_users.assert_called_once_with()


@pytest.fixture
def celery(patch, pyramid_request):
    cel = patch("h.tasks.cleanup.celery", autospec=False)
    cel.request = pyramid_request
    return cel


@pytest.fixture(autouse=True)
def newrelic(mocker):
    return mocker.patch("h.tasks.cleanup.newrelic")
