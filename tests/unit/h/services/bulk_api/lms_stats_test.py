from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.services.bulk_api.lms_stats import (
    AssignmentStats,
    BulkLMSStatsService,
    service_factory,
)


class TestBulkLMSStatsService:
    def test_it(self, svc, group, user, annotation, annotation_reply, reply_user):
        stats = svc.assignment_stats(
            groups=[group.authority_provided_id], assignment_id="ASSIGNMENT_ID"
        )

        assert stats == [
            AssignmentStats(
                userid=user.userid,
                display_name=user.display_name,
                annotations=1,
                replies=0,
                last_activity=annotation.created,
            ),
            AssignmentStats(
                userid=reply_user.userid,
                display_name=reply_user.display_name,
                annotations=0,
                replies=1,
                last_activity=annotation_reply.created,
            ),
        ]

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def reply_user(self, factories):
        return factories.User()

    @pytest.fixture
    def annotation(self, factories, user, group):
        anno = factories.Annotation(group=group)
        anno_slim = factories.AnnotationSlim(
            annotation=anno,
            user=user,
            deleted=False,
            shared=True,
            moderated=False,
            group=group,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim,
            data={"lms": {"assignment": {"resource_link_id": "ASSIGNMENT_ID"}}},
        )

        return anno_slim

    @pytest.fixture
    def annotation_reply(self, factories, reply_user, group, annotation):
        anno_reply = factories.Annotation(group=group, references=[annotation.id])
        anno_slim_reply = factories.AnnotationSlim(
            annotation=anno_reply,
            user=reply_user,
            deleted=False,
            shared=True,
            moderated=False,
            group=group,
        )
        factories.AnnotationMetadata(
            annotation_slim=anno_slim_reply,
            data={"lms": {"assignment": {"resource_link_id": "ASSIGNMENT_ID"}}},
        )

        return anno_slim_reply

    @pytest.fixture
    def svc(self, db_session):
        return BulkLMSStatsService(db_session, "example.com")


class TestServiceFactory:
    @pytest.mark.usefixtures("with_auth_client")
    def test_it(self, pyramid_request, BulkLMSStatsService):
        svc = service_factory(sentinel.context, pyramid_request)

        BulkLMSStatsService.assert_called_once_with(
            db=pyramid_request.db,
            authorized_authority=pyramid_request.identity.auth_client.authority,
        )
        assert svc == BulkLMSStatsService.return_value

    @pytest.fixture
    def BulkLMSStatsService(self, patch):
        return patch("h.services.bulk_api.lms_stats.BulkLMSStatsService")
