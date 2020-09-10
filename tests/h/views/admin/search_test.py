import datetime

import pytest

from h.views.admin.search import SearchAdminViews


class TestSearchAdminViews:
    def test_get(self, views):
        assert views.get() == {}

    def test_reindex_date(
        self, views, reindex_annotations_in_date_range, pyramid_request
    ):
        pyramid_request.params = {
            "start": "2020-09-09",
            "end": "2020-10-10",
        }

        template_variables = views.reindex_date()

        reindex_annotations_in_date_range.delay.assert_called_once_with(
            datetime.datetime(2020, 9, 9, 0, 0), datetime.datetime(2020, 10, 10, 0, 0)
        )
        assert pyramid_request.session.peek_flash("success") == [
            "Began reindexing from 2020-09-09 00:00:00 to 2020-10-10 00:00:00"
        ]
        assert template_variables == {"indexing": True, "task_id": 23}

    @pytest.fixture
    def views(self, pyramid_request):
        return SearchAdminViews(pyramid_request)


@pytest.fixture(autouse=True)
def reindex_annotations_in_date_range(patch):
    reindex_annotations_in_date_range = patch(
        "h.views.admin.search.reindex_annotations_in_date_range"
    )
    reindex_annotations_in_date_range.delay.return_value.id = 23
    return reindex_annotations_in_date_range
