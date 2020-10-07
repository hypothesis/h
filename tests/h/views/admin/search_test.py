import datetime

import pytest

from h.views.admin.search import SearchAdminViews


class TestSearchAdminViews:
    def test_get(self, views):
        assert views.get() == {}

    def test_reindex_date(self, views, search_index, pyramid_request):
        pyramid_request.params = {
            "start": "2020-09-09",
            "end": "2020-09-11",
        }

        views.reindex_date()

        search_index.add_annotations_between_times.assert_called_once_with(
            datetime.datetime(year=2020, month=9, day=9),
            datetime.datetime(year=2020, month=9, day=11),
        )
        assert pyramid_request.session.peek_flash("success") == [
            "Began reindexing from 2020-09-09 00:00:00 to 2020-09-11 00:00:00"
        ]

    @pytest.fixture
    def views(self, pyramid_request):
        return SearchAdminViews(pyramid_request)


pytestmark = pytest.mark.usefixtures("search_index")
