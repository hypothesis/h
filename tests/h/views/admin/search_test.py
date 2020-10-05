import datetime

import pytest
from h_matchers import Any

from h.views.admin.search import SearchAdminViews


class TestSearchAdminViews:
    def test_get(self, views):
        assert views.get() == {}

    def test_reindex_date(self, annotation_ids, views, job_queue, pyramid_request):
        pyramid_request.params = {
            "start": "2020-09-09",
            "end": "2020-09-11",
        }

        views.reindex_date()

        job_queue.add_sync_annotation_jobs.assert_called_once_with(
            Any.list.containing(annotation_ids).only(),
            "reindex_date",
        )
        assert pyramid_request.session.peek_flash("success") == [
            "Scheduled reindexing of 10 annotations"
        ]

    @pytest.fixture
    def annotations(self, factories):
        return factories.Annotation.create_batch(
            size=10, updated=datetime.datetime(year=2020, month=9, day=10)
        )

    @pytest.fixture(autouse=True)
    def non_matching_annotations(self, factories):
        """Annotations from outside the date range that we're reindexing."""
        before_annotations = factories.Annotation.create_batch(
            size=3, updated=datetime.datetime(year=2020, month=9, day=8)
        )
        after_annotations = factories.Annotation.create_batch(
            size=3, updated=datetime.datetime(year=2020, month=9, day=12)
        )
        return before_annotations + after_annotations

    @pytest.fixture
    def annotation_ids(self, annotations):
        return [annotation.id for annotation in annotations]

    @pytest.fixture
    def views(self, pyramid_request):
        return SearchAdminViews(pyramid_request)


pytestmark = pytest.mark.usefixtures("job_queue")
