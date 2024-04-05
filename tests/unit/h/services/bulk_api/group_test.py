from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.services.bulk_api.group import BulkGroup, BulkGroupService, service_factory


class TestBulkGroupService:
    def test_it(self, svc, factories):
        since = datetime(2023, 1, 1)
        group = factories.Group()
        group_without_annos = factories.Group()
        group_with_annos_in_other_dates = factories.Group()
        another_group = factories.Group()
        factories.Annotation(group=group, created=since + timedelta(days=1))
        factories.Annotation(
            group=group_with_annos_in_other_dates, created=since - timedelta(days=1)
        )

        groups = svc.group_search(
            groups=[
                group.authority_provided_id,
                group_without_annos.authority_provided_id,
                group_with_annos_in_other_dates.authority_provided_id,
                another_group.authority_provided_id,
            ],
            annotations_created={"gt": "2023-01-01", "lte": "2023-12-31"},
        )

        assert groups == [BulkGroup(authority_provided_id=group.authority_provided_id)]

    @pytest.fixture
    def svc(self, db_session):
        return BulkGroupService(db_session)


class TestServiceFactory:
    def test_it(self, pyramid_request, BulkGroupService):
        svc = service_factory(sentinel.context, pyramid_request)

        BulkGroupService.assert_called_once_with(db_replica=pyramid_request.db_replica)
        assert svc == BulkGroupService.return_value

    @pytest.fixture
    def BulkGroupService(self, patch):
        return patch("h.services.bulk_api.group.BulkGroupService")
