import json

import pytest


@pytest.mark.usefixtures("with_clean_db_and_search_index")
class TestBulkAnnotationCounts:
    @pytest.mark.parametrize("empty_filter", ["groups", "assignment_ids", "h_userids"])
    def test_empty_list_filter_is_rejected(
        self, app, auth_header_for_authority, empty_filter
    ):
        filters = {"groups": ["group-id"], empty_filter: []}

        response = app.post(
            "/api/bulk/lms/annotations",
            json.dumps({"group_by": "user", "filter": filters}),
            headers=auth_header_for_authority("lms.hypothes.is"),
            content_type="application/json",
            expect_errors=True,
        )

        assert response.status_int == 400
