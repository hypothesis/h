from datetime import datetime

import pytest

from h.services.bulk_api.lms_stats import AnnotationCounts, CountsGroupBy
from h.views.api.bulk.stats import AssignmentStatsSchema, get_annotation_counts


class TestSchema:
    def test_it_is_a_valid_schema(self, schema):
        # Extremely basic self checking that this is a valid JSON schema
        assert not schema.validator.check_schema(schema.schema)

    @pytest.fixture
    def schema(self):
        return AssignmentStatsSchema()


@pytest.mark.usefixtures("bulk_stats_service", "with_auth_client")
class TestBulkGroup:
    def test_get_annotation_counts(
        self, pyramid_request, assignment_request, bulk_stats_service
    ):
        bulk_stats_service.get_annotation_counts.return_value = [
            AnnotationCounts(
                assignment_id="ASSIGNMENT",
                display_name=f"display_name{i}",
                userid=i,
                annotations=i,
                replies=i,
                page_notes=i,
                last_activity=datetime.now(),
            )
            for i in range(3)
        ]

        response = get_annotation_counts(pyramid_request)

        bulk_stats_service.get_annotation_counts.assert_called_once_with(
            group_by=CountsGroupBy.USER,
            groups=assignment_request["filter"]["groups"],
            assignment_ids=assignment_request["filter"]["assignment_ids"],
            h_userids=assignment_request["filter"]["h_userids"],
        )
        return_data = [
            {
                "assignment_id": row.assignment_id,
                "display_name": row.display_name,
                "userid": row.userid,
                "annotations": row.annotations,
                "replies": row.replies,
                "page_notes": row.page_notes,
                "last_activity": row.last_activity.isoformat(),
            }
            for row in bulk_stats_service.get_annotation_counts.return_value
        ]
        assert response.json == return_data
        assert response.status_code == 200
        assert response.content_type == "application/x-ndjson"

    @pytest.fixture
    def assignment_request(self, pyramid_request):
        pyramid_request.json = {
            "group_by": "user",
            "filter": {
                "groups": ["3a022b6c146dfd9df4ea8662178eac"],
                "h_userids": ["acc:user@authority"],
                "assignment_ids": ["ASSIGNMENT_ID"],
            },
        }

        return pyramid_request.json
