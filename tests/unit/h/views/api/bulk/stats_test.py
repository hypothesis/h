from datetime import datetime

import pytest

from h.schemas.base import ValidationError
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
                last_activity=datetime.now(),  # noqa: DTZ005
            )
            for i in range(3)
        ]

        response = get_annotation_counts(pyramid_request)

        bulk_stats_service.get_annotation_counts.assert_called_once_with(
            group_by=CountsGroupBy.USER,
            groups=assignment_request["filter"]["groups"],
            assignment_ids=assignment_request["filter"]["assignment_ids"],
            h_userids=assignment_request["filter"]["h_userids"],
            document_uri=None,
            due_date=None,
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

    @pytest.mark.parametrize(
        ("due_date", "expected"),
        [
            # Whatever the offset, the bound reaches the service as the naive
            # UTC that AnnotationSlim.created is stored in.
            ("2026-04-05T23:59:00+00:00", datetime(2026, 4, 5, 23, 59)),  # noqa: DTZ001
            ("2026-04-05T20:59:00-03:00", datetime(2026, 4, 5, 23, 59)),  # noqa: DTZ001
            # What the LMS sends: JS toISOString().
            ("2026-04-05T23:59:00.000Z", datetime(2026, 4, 5, 23, 59)),  # noqa: DTZ001
        ],
    )
    def test_get_annotation_counts_normalises_the_due_date(
        self,
        pyramid_request,
        assignment_request,
        bulk_stats_service,
        due_date,
        expected,
    ):
        assignment_request["filter"]["due_date"] = due_date
        bulk_stats_service.get_annotation_counts.return_value = []

        get_annotation_counts(pyramid_request)

        passed = bulk_stats_service.get_annotation_counts.call_args.kwargs["due_date"]
        assert passed == expected
        # Naive, so the comparison can't depend on the DB session's timezone.
        assert passed.tzinfo is None

    def test_get_annotation_counts_rejects_a_due_date_without_an_offset(
        self, pyramid_request, assignment_request
    ):
        assignment_request["filter"]["due_date"] = "2026-04-05T23:59:00"

        with pytest.raises(ValidationError):
            get_annotation_counts(pyramid_request)

    def test_get_annotation_counts_rejects_user_phase_without_a_document(
        self, pyramid_request, assignment_request
    ):
        assignment_request["group_by"] = "user_phase"

        with pytest.raises(ValidationError):
            get_annotation_counts(pyramid_request)

    @pytest.mark.parametrize("assignment_ids", [["A", "B"], [], None])
    def test_get_annotation_counts_rejects_a_document_without_one_assignment(
        self, pyramid_request, assignment_request, assignment_ids
    ):
        # A checkpoint's reveal date is only meaningful for a single
        # (group, document) pair.
        assignment_request["group_by"] = "user_phase"
        assignment_request["filter"]["document_uri"] = "http://example.com/reading"
        assignment_request["filter"]["assignment_ids"] = assignment_ids

        with pytest.raises(ValidationError):
            get_annotation_counts(pyramid_request)

    def test_get_annotation_counts_rejects_non_string_assignment_ids(
        self, pyramid_request, assignment_request
    ):
        assignment_request["filter"]["assignment_ids"] = [1, 2]

        with pytest.raises(ValidationError):
            get_annotation_counts(pyramid_request)

    @pytest.mark.usefixtures("assignment_request")
    def test_get_annotation_counts_turns_a_service_rejection_into_a_400(
        self, pyramid_request, bulk_stats_service
    ):
        bulk_stats_service.get_annotation_counts.side_effect = ValueError("nope")

        with pytest.raises(ValidationError):
            get_annotation_counts(pyramid_request)

    def test_get_annotation_counts_by_user_phase(
        self, pyramid_request, assignment_request, bulk_stats_service
    ):
        assignment_request["group_by"] = "user_phase"
        assignment_request["filter"]["document_uri"] = "http://example.com/reading"
        reveal_date = datetime(2026, 3, 10, 9, 0)  # noqa: DTZ001
        bulk_stats_service.get_annotation_counts.return_value = [
            AnnotationCounts(
                userid="acct:user@authority",
                display_name="UserName",
                phase=1,
                ends_at=reveal_date,
                annotations=4,
                replies=2,
                page_notes=0,
                last_activity=reveal_date,
            ),
            AnnotationCounts(
                userid="acct:user@authority",
                display_name="UserName",
                phase=2,
                ends_at=None,
                annotations=8,
                replies=1,
                page_notes=0,
                last_activity=None,
            ),
        ]

        response = get_annotation_counts(pyramid_request)

        assert response.json == [
            {
                "assignment_id": None,
                "userid": "acct:user@authority",
                "display_name": "UserName",
                "phase": 1,
                "ends_at": reveal_date.isoformat(),
                "annotations": 4,
                "replies": 2,
                "page_notes": 0,
                "last_activity": reveal_date.isoformat(),
            },
            {
                "assignment_id": None,
                "userid": "acct:user@authority",
                "display_name": "UserName",
                "phase": 2,
                # Not revealed or no due date: the boundary isn't known yet.
                "ends_at": None,
                "annotations": 8,
                "replies": 1,
                "page_notes": 0,
                "last_activity": None,
            },
        ]

    @pytest.mark.usefixtures("assignment_request")
    def test_get_annotation_counts_by_user_omits_the_phase_fields(
        self, pyramid_request, bulk_stats_service
    ):
        bulk_stats_service.get_annotation_counts.return_value = [
            AnnotationCounts(
                userid="acct:user@authority",
                display_name="UserName",
                annotations=4,
                replies=2,
                page_notes=0,
                last_activity=datetime(2026, 3, 10, 9, 0),  # noqa: DTZ001
            )
        ]

        response = get_annotation_counts(pyramid_request)

        assert "phase" not in response.json[0]
        assert "ends_at" not in response.json[0]

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
